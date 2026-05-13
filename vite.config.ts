import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: '/Simposio_Extensao_Unifametro/',
  plugins: [react()],
})
