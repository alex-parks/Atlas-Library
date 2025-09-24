import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3011,
    host: true,
    // Add this line to allow your custom host
    allowedHosts: ['library.blacksmith.tv'], 
  }
})
