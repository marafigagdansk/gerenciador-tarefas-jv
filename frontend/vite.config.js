import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ mode }) => {
  // Carrega variáveis do arquivo .env da raiz do projeto e do diretório local
  const env = loadEnv(mode, path.resolve(__dirname, '..'), '')
  
  const frontendPort = parseInt(env.FRONTEND_PORT, 10) || 5173
  const backendHost = env.BACKEND_HOST || '127.0.0.1'
  const backendPort = env.BACKEND_PORT || '8000'
  const backendTarget = env.VITE_API_URL || `http://${backendHost}:${backendPort}`

  return {
    plugins: [vue()],
    envDir: path.resolve(__dirname, '..'),
    server: {
      port: frontendPort,
      proxy: {
        '/api': {
          target: backendTarget,
          changeOrigin: true,
        }
      }
    }
  }
})
