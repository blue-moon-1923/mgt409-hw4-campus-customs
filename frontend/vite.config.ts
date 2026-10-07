import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The backend owns /api (JSON) and /images (product photos). Proxying both keeps
// the frontend on relative URLs, so no base URL is hard-coded in the components.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/images': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
