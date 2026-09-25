import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig(({ command }) => ({
  // На сервере админка открывается на /admin/ (docker/nginx/conf.d/marshruty.conf):
  // скрипты и стили должны запрашиваться оттуда, а не из корня сайта.
  base: command === 'build' ? '/admin/' : '/',
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
}))
