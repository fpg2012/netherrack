import imageCompression from 'browser-image-compression'
// 让压缩库的 Web Worker 从本站加载，而不是默认的 jsDelivr CDN。
// 这样离线/被墙时也能在 worker 里压缩，不会退回主线程。
import compressionLibUrl from 'browser-image-compression/dist/browser-image-compression.js?url'
// Canvas 只能拿到 GIF 第一帧，所以动图交给 gif2webp（libwebp 的 WASM 版）。
// 它在自己的 worker 里跑，保留所有帧、透明度和循环设置。
import { gif2webp } from '@btheegg-kimth/gif2webp/worker'

/** 超过这个大小就转成 WebP，即使还没碰到上传上限。 */
export const COMPRESS_OVER_BYTES = 1024 * 1024
/** 后端 /uploads 的单个附件上限。 */
export const UPLOAD_MAX_BYTES = 5 * 1024 * 1024

const MAX_EDGE = 2560
// 比较激进的质量，优先减小体积。
const INITIAL_QUALITY = 0.55

export interface CompressedImage {
  file: File
  compressed: boolean
  originalSize: number
  wasGif: boolean
}

export function shouldCompressImage(file: File): boolean {
  if (!file.type.startsWith('image/')) return false
  return file.type === 'image/gif' || file.size > COMPRESS_OVER_BYTES
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function webpName(name: string): string {
  return `${name.replace(/\.[^./\\]+$/, '') || 'image'}.webp`
}

function preparedFile(data: BlobPart | Uint8Array, name: string, lastModified: number): File {
  return new File([data as BlobPart], webpName(name), { type: 'image/webp', lastModified })
}

// 动图（表情包）不追求画质，直接压分辨率和质量；
// 第一档就能把绝大多数 GIF 压到几百 KB，后两档只兜底超大文件。
const GIF_ATTEMPTS = [
  { quality: 55, edge: 800 },
  { quality: 42, edge: 640 },
  { quality: 32, edge: 480 },
] as const

/** 转码动图（保留帧、透明度和循环）。 */
async function compressGif(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<File> {
  let reported = 0
  const report = (percent: number) => {
    if (percent <= reported) return
    reported = percent
    onProgress?.(percent)
  }

  report(5)
  const bytes = new Uint8Array(await file.arrayBuffer())
  report(15)

  // gif2webp 不提供逐帧进度；用一个不阻塞的计时器做平滑的估算。
  let estimate = 15
  const timer = globalThis.setInterval(() => {
    estimate = Math.min(90, estimate + Math.max(1, Math.round((90 - estimate) * 0.08)))
    report(estimate)
  }, 300)

  try {
    let lastSize = 0
    for (const attempt of GIF_ATTEMPTS) {
      let output: Uint8Array
      try {
        output = await gif2webp(bytes, {
          lossy: true,
          quality: attempt.quality,
          method: 4,
          resize: { width: attempt.edge, height: attempt.edge },
        })
      } catch (err) {
        const detail = err instanceof Error ? err.message : String(err)
        throw new Error(`GIF 转码失败：${detail}`)
      }
      lastSize = output.byteLength
      if (lastSize <= UPLOAD_MAX_BYTES) {
        report(100)
        return preparedFile(output, file.name, file.lastModified)
      }
    }
    throw new Error(
      `GIF 转码后仍有 ${formatBytes(lastSize)}，超过 ${formatBytes(UPLOAD_MAX_BYTES)} 上限，已拒绝上传`,
    )
  } finally {
    globalThis.clearInterval(timer)
  }
}

/**
 * 把超过 1 MB 的图片（以及所有 GIF）压缩/转码成 WebP。
 * 真正的解码与编码在 Web Worker 中进行，不阻塞页面渲染。
 */
export async function compressImageForUpload(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<CompressedImage> {
  if (!shouldCompressImage(file)) {
    if (file.size > UPLOAD_MAX_BYTES) {
      throw new Error(`文件超过 ${formatBytes(UPLOAD_MAX_BYTES)}，无法上传`)
    }
    return { file, compressed: false, originalSize: file.size, wasGif: false }
  }

  if (file.type === 'image/gif') {
    const prepared = await compressGif(file, onProgress)
    return {
      file: prepared,
      compressed: true,
      originalSize: file.size,
      wasGif: true,
    }
  }

  let output: File
  try {
    output = await imageCompression(file, {
      // 达到后端上限时库会自动继续降低质量/分辨率
      maxSizeMB: UPLOAD_MAX_BYTES / 1024 / 1024,
      maxWidthOrHeight: MAX_EDGE,
      useWebWorker: true,
      fileType: 'image/webp',
      initialQuality: INITIAL_QUALITY,
      maxIteration: 10,
      libURL: compressionLibUrl,
      onProgress: (percent) => onProgress?.(Math.round(percent)),
    })
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err)
    throw new Error(`图片压缩失败：${detail}`)
  }

  if (output.type !== 'image/webp') {
    throw new Error('当前浏览器不支持 WebP 编码，无法压缩图片')
  }

  const prepared = preparedFile(output, file.name, file.lastModified)

  if (prepared.size > UPLOAD_MAX_BYTES) {
    throw new Error(
      `压缩后仍有 ${formatBytes(prepared.size)}，超过 ${formatBytes(UPLOAD_MAX_BYTES)} 上限，已拒绝上传`,
    )
  }

  return {
    file: prepared,
    compressed: true,
    originalSize: file.size,
    wasGif: file.type === 'image/gif',
  }
}
