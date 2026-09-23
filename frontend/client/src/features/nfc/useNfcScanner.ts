import type { PluginListenerHandle } from '@capacitor/core'
import { onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'

import { errorText } from '@/core/format'

import {
  consumeLaunchTag,
  isNfcAvailable,
  nfcStatus,
  onNfcTag,
  startNfcScan,
  stopNfcScan,
  type NfcStatus,
  type NfcTag,
} from './nfc'

/**
 * Экран ловит метки, пока открыт.
 *
 * Слушать начинаем сразу: разрешений NFC не требует, а держать режим чтения
 * дольше экрана нельзя — Android отдаёт метки только активному экрану. Метку,
 * которой открыли приложение, забираем при первом же открытии экрана.
 */
export function useNfcScanner(onTag?: (tag: NfcTag) => void) {
  const available = isNfcAvailable()
  const status = ref<NfcStatus>({ supported: available, enabled: false })
  const scanning = ref(false)
  const error = ref<string | null>(null)
  const lastTag = shallowRef<NfcTag | null>(null)

  let listener: PluginListenerHandle | null = null

  function accept(tag: NfcTag): void {
    lastTag.value = tag
    // Короткий отклик: человек держит телефон у таблички и на экран не смотрит.
    navigator.vibrate?.(60)
    onTag?.(tag)
  }

  async function refreshStatus(): Promise<void> {
    if (!available) return
    try {
      status.value = await nfcStatus()
    } catch (reason) {
      error.value = errorText(reason)
    }
  }

  async function start(): Promise<void> {
    if (!available || scanning.value) return
    try {
      listener ??= await onNfcTag(accept)
      await startNfcScan()
      scanning.value = true
      error.value = null
    } catch (reason) {
      scanning.value = false
      error.value = errorText(reason)
    }
  }

  async function stop(): Promise<void> {
    if (!available) return
    scanning.value = false
    try {
      await stopNfcScan()
    } catch {
      // Экран уже закрыт или NFC выключили — слушать всё равно нечего.
    }
    await listener?.remove()
    listener = null
  }

  onMounted(async () => {
    await refreshStatus()
    if (status.value.enabled) await start()
    const launched = await consumeLaunchTag()
    if (launched) accept(launched)
  })

  onBeforeUnmount(() => void stop())

  return { available, status, scanning, error, lastTag, start, stop, refreshStatus }
}
