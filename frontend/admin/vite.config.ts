import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    // Путь от корня проекта — так конфиг не тянет @types/node ради fileURLToPath.
    alias: { '@': '/src' },
  },
  server: {
    port: 5173,
    // Порт зафиксирован: он прописан в CORS_ORIGINS у admin_service.
    strictPort: true,
  },
})
