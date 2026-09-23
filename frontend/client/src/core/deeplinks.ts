import { App } from '@capacitor/app'
import { Capacitor } from '@capacitor/core'
import type { Router } from 'vue-router'

/** Схема ссылок приложения — та же, что в `AndroidManifest.xml`. */
const SCHEME = 'marshruty:'

/**
 * Ссылки `marshruty://…` открывают экран приложения: `marshruty://auth/external?…`
 * → `/auth/external?…`. Так в APK возвращаются из браузера после входа через
 * VK ID или Госуслуги. В браузере ссылок нет — там возврат обычной навигацией.
 */
export function listenDeepLinks(router: Router): void {
  if (!Capacitor.isNativePlatform()) return
  void App.addListener('appUrlOpen', ({ url }) => {
    let parsed: URL
    try {
      parsed = new URL(url)
    } catch {
      return
    }
    if (parsed.protocol !== SCHEME) return
    const path = `/${parsed.host}${parsed.pathname}`.replace(/\/+$/, '') || '/'
    void router.push(`${path}${parsed.search}`)
  })
}
