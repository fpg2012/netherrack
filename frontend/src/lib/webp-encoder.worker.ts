import encode, { init } from '@jsquash/webp/encode'
import wasmUrl from '@jsquash/webp/codec/enc/webp_enc.wasm?url'
import simdWasmUrl from '@jsquash/webp/codec/enc/webp_enc_simd.wasm?url'

interface EncodeRequest {
  buffer: ArrayBuffer
  width: number
  height: number
  quality: number
}

const scope = self as unknown as {
  onmessage: ((event: MessageEvent<EncodeRequest>) => void) | null
  postMessage(message: unknown, transfer?: Transferable[]): void
}

let ready: Promise<unknown> | null = null

function ensureReady(): Promise<unknown> {
  ready ??= init({
    locateFile: (path: string) =>
      path.endsWith('webp_enc_simd.wasm') ? simdWasmUrl : wasmUrl,
  })
  return ready
}

scope.onmessage = async (event) => {
  const { buffer, width, height, quality } = event.data
  try {
    await ensureReady()
    const data = new Uint8ClampedArray(buffer)
    const image = { data, width, height } as unknown as ImageData
    const output = await encode(image, { quality, method: 4 })
    scope.postMessage({ type: 'done', buffer: output }, [output])
  } catch (error) {
    scope.postMessage({
      type: 'error',
      message: error instanceof Error ? error.message : String(error),
    })
  }
}
