import { onScopeDispose, ref } from 'vue'

export type ShakeStatus = 'idle' | 'listening' | 'denied' | 'unsupported'

export interface ShakeOptions {
  /** Сила рывка без учёта гравитации, м/с². Спокойная ходьба — 2–4, тряска — 15–25. */
  threshold?: number
  /** Сколько рывков подряд считать тряской. Один удар — это положили телефон на стол. */
  peaks?: number
  /** За какое время должны уложиться рывки, мс. */
  windowMs?: number
  /** Сколько молчать после срабатывания, мс, — одна тряска не уходит дважды. */
  cooldownMs?: number
}

/** Интервал, за который индикатор силы тряски гаснет, если датчик замолчал. */
const DECAY_INTERVAL_MS = 100

/**
 * Тряска телефона по акселерометру (`devicemotion`): работает и в браузере, и в APK.
 *
 * `onShake` получает момент тряски по `performance.now()` — из него считается
 * «тряхнули N мс назад» к моменту отправки. Слушать датчик начинает только
 * `start()`, вызванный из нажатия кнопки: на iPhone разрешение на датчик
 * движения иначе не спросить.
 */
export function useShake(onShake: (shakenAt: number) => void, options: ShakeOptions = {}) {
  const threshold = options.threshold ?? 13
  const requiredPeaks = options.peaks ?? 3
  const windowMs = options.windowMs ?? 1000
  const cooldownMs = options.cooldownMs ?? 2500

  const supported = typeof window !== 'undefined' && 'DeviceMotionEvent' in window
  const status = ref<ShakeStatus>(supported ? 'idle' : 'unsupported')
  /** Сила движения 0…1 — для индикатора на экране. */
  const intensity = ref(0)
  /** Датчик реально шлёт данные. На компьютере событие есть, а ускорений нет. */
  const sensorAlive = ref(false)

  let peaks: number[] = []
  let lastPeakAt = -Infinity
  let lastShakeAt = -Infinity
  let decayTimer: ReturnType<typeof setInterval> | undefined

  function fire(at: number): void {
    if (at - lastShakeAt < cooldownMs) return
    lastShakeAt = at
    peaks = []
    onShake(at)
  }

  function handleMotion(event: DeviceMotionEvent): void {
    const magnitude = motionMagnitude(event)
    if (magnitude === null) return
    sensorAlive.value = true
    intensity.value = Math.max(intensity.value, Math.min(1, magnitude / (threshold * 1.8)))

    const now = performance.now()
    // События датчика идут ~60 раз в секунду: всплески ближе 80 мс — это один рывок.
    if (magnitude < threshold || now - lastPeakAt < 80) return
    lastPeakAt = now
    peaks = [...peaks.filter((at) => now - at <= windowMs), now]
    if (peaks.length >= requiredPeaks) fire(now)
  }

  async function start(): Promise<void> {
    if (!supported || status.value === 'listening') return
    // iOS 13+: доступ к датчику движения спрашивается отдельно и только из нажатия.
    const motion = DeviceMotionEvent as unknown as { requestPermission?: () => Promise<string> }
    if (typeof motion.requestPermission === 'function') {
      try {
        if ((await motion.requestPermission()) !== 'granted') {
          status.value = 'denied'
          return
        }
      } catch {
        status.value = 'denied'
        return
      }
    }
    window.addEventListener('devicemotion', handleMotion)
    decayTimer = setInterval(() => {
      intensity.value = intensity.value < 0.02 ? 0 : intensity.value * 0.8
    }, DECAY_INTERVAL_MS)
    status.value = 'listening'
  }

  function stop(): void {
    if (supported) window.removeEventListener('devicemotion', handleMotion)
    clearInterval(decayTimer)
    intensity.value = 0
    if (status.value === 'listening') status.value = 'idle'
  }

  /** Встряхнуть кнопкой: там, где датчика нет (компьютер), и на демо. */
  function trigger(): void {
    intensity.value = 1
    fire(performance.now())
  }

  onScopeDispose(stop)

  return { status, intensity, sensorAlive, start, stop, trigger }
}

function motionMagnitude(event: DeviceMotionEvent): number | null {
  const pure = event.acceleration
  if (pure && pure.x !== null && pure.y !== null && pure.z !== null) {
    return Math.hypot(pure.x, pure.y, pure.z)
  }
  // Ускорения без гравитации нет — вычитаем g из полного.
  const withGravity = event.accelerationIncludingGravity
  if (withGravity && withGravity.x !== null && withGravity.y !== null && withGravity.z !== null) {
    return Math.abs(Math.hypot(withGravity.x, withGravity.y, withGravity.z) - 9.81)
  }
  return null
}
