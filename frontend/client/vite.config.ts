import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    // Путь от корня проекта — так конфиг не тянет @types/node ради fileURLToPath.
    alias: { '@': '/src' },
  },
  server: {
    // 5173 занят админкой: оба приложения должны запускаться одновременно.
    port: 5174,
    strictPort: true,
  },
})
