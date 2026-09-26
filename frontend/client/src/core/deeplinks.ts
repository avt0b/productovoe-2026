import { App } from '@capacitor/app'
import { Capacitor } from '@capacitor/core'
import type { Router } from 'vue-router'

/**
 * Путь экрана по ссылке приложения: `marshruty://auth/external?…` →
 * `/auth/external?…`. Чужая ссылка — `null`.
 *
 * Разбираем сами, а не через `URL`: WebView до 130-й версии не выделяет host у
 * нестандартных схем и отдаёт путь `//auth/external`, по которому экрана нет.
 */
export function appLinkPath(url: string | null | undefined): string | null {
  const match = /^marshruty:\/\/([^/?#]*)([^?#]*)(\?[^#]*)?/i.exec(url?.trim() ?? '')
  if (!match) return null
  const [, host, rest, search = ''] = match
  const path = `/${host}${rest}`.replace(/\/+$/, '') || '/'
  return `${path}${search}`
}

/**
 * Ссылки `marshruty://…` открывают экран приложения: `marshruty://auth/external?…`
 * → `/auth/external?…`. Так в APK возвращаются из браузера после входа через
 * VK ID или Госуслуги. В браузере ссылок нет — там возврат обычной навигацией.
 * Ссылки с NFC-меток приходят не сюда, а в `features/nfc` (`listenNfcLinks`).
 */
export function listenDeepLinks(router: Router): void {
  if (!Capacitor.isNativePlatform()) return
  void App.addListener('appUrlOpen', ({ url }) => {
    const path = appLinkPath(url)
    if (path) void router.push(path)
  })
}
