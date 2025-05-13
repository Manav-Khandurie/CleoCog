import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import tsConfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  plugins: [react(), tsConfigPaths()],
  base: "./",
  server: {
    allowedHosts: ['*'],
    host: true, // Allow access from any external host (IP, ngrok, etc.)
    port: 5173  // Optional: specify port
  },
  headers: {
    'Access-Control-Allow-Origin': '*',
  }
})
