import { gif2webp } from '@btheegg-kimth/gif2webp/worker'

/** 超过这个大小就转成 WebP，即使还没碰到上传上限。 */
export const COMPRESS_OVER_BYTES = 1024 * 1024
/** 后端 /uploads 的单个附件上限。 */
export const UPLOAD_MAX_BYTES = 5 * 1024 * 1024

// 长边限制在 1024；配合最低质量，正常图片很难碰到 5 MB 上限。
const MAX_EDGE = 1024
// libwebp 的质量范围是 0–100；直接用最低质量，优先减小体积。
const WEBP_QUALITY = 20

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

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve(img)
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('图片解码失败，可能是当前浏览器不支持该格式'))
    }
    img.src = url
  })
}

function drawImageData(img: HTMLImageElement, width: number, height: number): ImageData {
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const context = canvas.getContext('2d')
  if (!context) throw new Error('浏览器不支持 Canvas，无法压缩图片')
  context.drawImage(img, 0, 0, width, height)
  const data = context.getImageData(0, 0, width, height)
  // 及时释放大画布占用的内存。
  canvas.width = 0
  canvas.height = 0
  return data
}

interface EncodeMessage {
  type: 'done' | 'error'
  buffer?: ArrayBuffer
  message?: string
}

/**
 * 在 Web Worker 里用 libwebp（WASM）编码 WebP。
 * Safari 的 Canvas 不能编码 WebP，WASM 不依赖浏览器的编码能力。
 */
function encodeWebp(data: ImageData): Promise<ArrayBuffer> {
  return new Promise((resolve, reject) => {
    const worker = new Worker(
      new URL('./webp-encoder.worker.ts', import.meta.url),
      { type: 'module' },
    )

    const finish = () => worker.terminate()

    worker.onmessage = (event: MessageEvent<EncodeMessage>) => {
      const message = event.data
      finish()
      if (message.type === 'done' && message.buffer) {
        resolve(message.buffer)
      } else {
        reject(new Error(message.message || 'WebP 编码失败'))
      }
    }

    worker.onerror = (event) => {
      finish()
      reject(new Error(event.message || 'WebP 编码器加载失败'))
    }

    worker.postMessage(
      {
        buffer: data.data.buffer,
        width: data.width,
        height: data.height,
        quality: WEBP_QUALITY,
      },
      [data.data.buffer],
    )
  })
}

async function compressStaticImage(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<CompressedImage> {
  const img = await loadImage(file)
  onProgress?.(8)

  const naturalWidth = img.naturalWidth
  const naturalHeight = img.naturalHeight
  if (!naturalWidth || !naturalHeight) throw new Error('无法读取图片尺寸')

  const scale = Math.min(1, MAX_EDGE / Math.max(naturalWidth, naturalHeight))
  const width = Math.max(1, Math.round(naturalWidth * scale))
  const height = Math.max(1, Math.round(naturalHeight * scale))

  const data = drawImageData(img, width, height)
  onProgress?.(20)
  const buffer = await encodeWebp(data)
  const prepared = preparedFile(buffer, file.name, file.lastModified)

  if (prepared.size > UPLOAD_MAX_BYTES) {
    throw new Error(
      `压缩后仍有 ${formatBytes(prepared.size)}，超过 ${formatBytes(UPLOAD_MAX_BYTES)} 上限，已拒绝上传`,
    )
  }

  onProgress?.(100)
  return {
    file: prepared,
    compressed: true,
    originalSize: file.size,
    wasGif: false,
  }
}

/**
 * 把超过 1 MB 的图片（以及所有 GIF）压缩/转码成 WebP。
 * 静态图用 libwebp 的 WASM 在 Worker 中编码，不依赖 Canvas 的 WebP 支持。
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

  return compressStaticImage(file, onProgress)
}
