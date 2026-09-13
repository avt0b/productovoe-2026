import { onScopeDispose, ref, shallowRef } from 'vue'

import type { UserPosition } from './types'

export type GeolocationStatus = 'idle' | 'locating' | 'ready' | 'denied' | 'unavailable'

/**
 * Где пользователь.
 *
 * Само ничего не спрашивает: разрешение запрашивается только по кнопке «Где я».
 * Иначе системный диалог выскакивает при первом же открытии карты, и половина
 * людей жмёт «Запретить», не поняв зачем.
 */
export function useGeolocation() {
  const position = shallowRef<UserPosition | null>(null)
  const status = ref<GeolocationStatus>('idle')
  let watchId: number | null = null

  function start(): void {
    if (watchId !== null) return
    if (!('geolocation' in navigator)) {
      status.value = 'unavailable'
      return
    }
    status.value = position.value ? 'ready' : 'locating'
    watchId = navigator.geolocation.watchPosition(
      (fix) => {
        position.value = {
          lat: fix.coords.latitude,
          lon: fix.coords.longitude,
          accuracyMeters: fix.coords.accuracy,
        }
        status.value = 'ready'
      },
      (error) => {
        if (error.code === error.PERMISSION_DENIED) {
          status.value = 'denied'
          stop()
        } else if (!position.value) {
          // Нет спутников или истёк таймаут — слежение продолжается, фикс может прийти позже.
          status.value = 'unavailable'
        }
      },
      { enableHighAccuracy: true, maximumAge: 10_000, timeout: 20_000 },
    )
  }

  function stop(): void {
    if (watchId !== null) navigator.geolocation.clearWatch(watchId)
    watchId = null
  }

  onScopeDispose(stop)

  return { position, status, start, stop }
}

/** Что сказать человеку, если определить место не вышло. */
export function geolocationProblem(status: GeolocationStatus): string | null {
  if (status === 'denied') return 'Доступ к геолокации запрещён — разрешите его в настройках телефона или браузера'
  if (status === 'unavailable') return 'Не удалось определить местоположение — выйдите на открытое место'
  return null
}
