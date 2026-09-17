import type { CapacitorConfig } from '@capacitor/cli'

/**
 * APK клиента: та же сборка Vite, завёрнутая в Android WebView.
 *
 * Приложение открывается с `https://localhost` — этот origin разрешён в
 * CORS_ORIGINS у `map_service` и `route_service`.
 */
const config: CapacitorConfig = {
  appId: 'ru.marshruty.client',
  appName: 'Маршруты победы',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    // Сервисы на хакатоне подняты по http в локальной сети. В проде — только https,
    // и эти два флага (здесь и `allowMixedContent` ниже) надо убрать.
    cleartext: true,
  },
  android: {
    // Страница с https://localhost ходит в http://<компьютер>:8003 — без этого WebView блокирует запросы.
    allowMixedContent: true,
  },
}

export default config
