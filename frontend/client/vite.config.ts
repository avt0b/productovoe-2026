import vue from '@vitejs/plugin-vue'
import { defineConfig, loadEnv } from 'vite'

/** Адреса сервисов, без которых APK бесполезен. */
const SERVICE_URL_KEYS = [
  'VITE_AUTH_API_URL',
  'VITE_USER_API_URL',
  'VITE_MAP_API_URL',
  'VITE_HQ_API_URL',
  'VITE_ARCHIVE_API_URL',
  'VITE_ROUTE_API_URL',
  'VITE_MEDIA_API_URL',
]

const LOOPBACK = /\/\/(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])([:/]|$)/i

/**
 * Сборка APK с адресами по умолчанию молча даёт нерабочее приложение:
 * `127.0.0.1` на телефоне — это сам телефон, а поменять адрес внутри
 * приложения больше нечем. Поэтому в режиме `android` требуем адреса явно.
 */
function checkAndroidEnv(mode: string): void {
  if (mode !== 'android') return
  const env = loadEnv(mode, '.', 'VITE_')
  const missing = SERVICE_URL_KEYS.filter((key) => !env[key] || LOOPBACK.test(env[key]))
  if (missing.length === 0) return
  throw new Error(
    [
      'Сборка APK остановлена: адреса сервисов не заданы или указывают на сам телефон.',
      `Проверьте .env.android.local (образец — .env.android.example): ${missing.join(', ')}.`,
      'Нужен адрес компьютера или сервера в сети, например http://192.168.1.10:8001.',
    ].join('\n'),
  )
}

export default defineConfig(({ mode }) => {
  checkAndroidEnv(mode)
  return {
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
  }
})
