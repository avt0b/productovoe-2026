import { App } from '@capacitor/app'
import type { PluginListenerHandle } from '@capacitor/core'
import { onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { appPath, consumeLaunchTag, isNfcAvailable, onNfcTag, tagPayload } from '@/features/nfc'

/** Экран выдачи звания — модуль `role-grant`. */
const GRANT_ROUTE = 'role-grant'
/** Экран «NFC-метка»: там метки пишут и проверяют. */
const NFC_ROUTE = 'nfc'

/** `marshruty://grant?k=…` → `/grant?k=…`. Любая другая ссылка — null. */
export function grantPath(uri: string | null | undefined): string | null {
  const path = appPath(uri ?? undefined)
  return path === '/grant' || path?.startsWith('/grant?') ? path : null
}

/**
 * Метка звания открывает экран выдачи, где бы человек ни был.
 *
 * Обычные ссылки `marshruty://…` ведёт `core/deeplinks.ts`, но метку Android
 * присылает другим событием (NDEF_DISCOVERED), и `appUrlOpen` Capacitor на
 * неё молчит. Поэтому:
 *
 * - приложение открыли меткой — ссылка есть в `App.getLaunchUrl()`. Саму
 *   метку забираем у NFC-плагина, только если она наша: чужую он бережёт для
 *   экрана «NFC-метка»;
 * - приложение уже открыто — метка приходит событием плагина.
 *
 * На экране «NFC-метка» молчим: там записанную метку прикладывают ещё раз
 * для проверки, и звание получил бы тот, кто метки пишет.
 */
export function useGrantTags(): void {
  const router = useRouter()
  const route = useRoute()
  let listener: PluginListenerHandle | null = null
  let disposed = false

  function open(path: string | null): void {
    if (!path || route.name === NFC_ROUTE || !router.hasRoute(GRANT_ROUTE)) return
    void router.push(path)
  }

  onMounted(async () => {
    if (!isNfcAvailable()) return
    const launch = await App.getLaunchUrl().catch(() => undefined)
    const launched = grantPath(launch?.url)
    if (launched) {
      await consumeLaunchTag()
      open(launched)
    }
    const handle = await onNfcTag((tag) => open(grantPath(tagPayload(tag)?.uri)))
    if (disposed) void handle.remove()
    else listener = handle
  })

  onBeforeUnmount(() => {
    disposed = true
    void listener?.remove()
  })
}
