import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// /api 保留完整路径，转发给 FastAPI。
export default defineConfig({
  plugins: [react()],
  server: {
    host: 'localhost',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
