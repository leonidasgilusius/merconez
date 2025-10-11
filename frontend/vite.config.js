import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5006', // orchestration_service
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
      '/intelligence': {
        target: 'http://127.0.0.1:5005', // optional - intelligence_service
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/intelligence/, '/api'),
      },
      '/realtime': {
        target: 'http://127.0.0.1:5007', // realtime_service (for websockets later)
        changeOrigin: true,
        ws: true, // websocket support
      },
    },
  },
})
