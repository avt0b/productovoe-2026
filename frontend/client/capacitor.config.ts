import { readFileSync } from 'node:fs'

import type { CapacitorConfig } from '@capacitor/cli'

/**
 * APK клиента: та же сборка Vite, завёрнутая в Android WebView.
 *
 * Приложение открывается с `https://localhost`, а на стенде, где сервисы подняты
 * по http, — с `http://localhost`. Оба origin (и `capacitor://localhost`)
 * разрешены в CORS_ORIGINS у всех сервисов.
 */

/**
 * Сервисы в `.env.android.local` по http — значит, и страницу открываем по http.
 *
 * На https-странице WebView пропускает к http-сервисам только запросы API, а
 * картинки, аудио и видео из MinIO блокирует («Mixed Content… blocked»):
 * аватарка загружалась и сохранялась, но не показывалась. `http://localhost`
 * WebView считает безопасным источником — геолокация и прочие API, которым
 * нужен secure context, работают так же, как на https.
 */
function servicesOverHttp(): boolean {
  try {
    return /^VITE_\w+_API_URL=http:\/\//m.test(readFileSync('.env.android.local', 'utf8'))
  } catch {
    return false
  }
}

const config: CapacitorConfig = {
  appId: 'ru.marshruty.client',
  appName: 'Маршруты победы',
  webDir: 'dist',
  server: {
    // Смена схемы — это смена origin: сессия из прежней сборки не переедет,
    // войти придётся заново.
    androidScheme: servicesOverHttp() ? 'http' : 'https',
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
