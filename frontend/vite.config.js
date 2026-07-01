import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/auth': 'http://127.0.0.1:8000',
      '/claims': 'http://127.0.0.1:8000',
      '/fraud': 'http://127.0.0.1:8000',
      '/risk': 'http://127.0.0.1:8000',
      '/renewal': 'http://127.0.0.1:8000',
      '/crop': 'http://127.0.0.1:8000',
      '/automation': 'http://127.0.0.1:8000',
    }
  }
})
