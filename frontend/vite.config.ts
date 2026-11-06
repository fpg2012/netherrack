import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // gif2webp 的 Worker 入口在 dev 预打包时会丢路径，排除后由 Vite 直接处理
  optimizeDeps: {
    exclude: ['@btheegg-kimth/gif2webp'],
  },
  // @jsquash/webp 里有动态 import 的 wasm 编解码器，Worker 需要 ES 格式才能分包
  worker: {
    format: 'es',
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/media': 'http://127.0.0.1:8000',
    },
  },
})
