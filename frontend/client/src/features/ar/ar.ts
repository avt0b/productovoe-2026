import { Capacitor, registerPlugin } from '@capacitor/core'

/** Точка, которую показываем в AR. Поля — то, что понимает `mobile/ar`. */
export interface ArPoint {
  pointId: string
  title: string
  stepIndex: number
  stepTotal: number
  /** Куда вести: место на земле. `null` — цели нет, только рассказ. */
  target: { lat: number; lon: number; label: string } | null
  /**
   * Проводник рядом с человеком. `null` — маскота быть не должно: у братской
   * могилы и мемориала он читается как неуважение.
   */
  companion: { name: string; subtitle: string; asset: string } | null
  narration: { audioUrl: string | null; subtitles: ArSubtitle[] }
  /** Печатная табличка на точке: проводник встаёт на неё через ARCore. */
  marker: { asset: string; widthMeters?: number; fallbackAfterMs?: number } | null
}

export interface ArSubtitle {
  fromMs: number
  toMs: number
  text: string
}

export type ArOutcome = 'completed' | 'dismissed' | 'unavailable'

export interface ArResult {
  outcome: ArOutcome
  pointId: string
  /** Почему AR не открылся: нет разрешения на камеру, нет камеры, нет компаса. */
  reason?: 'CAMERA_PERMISSION_DENIED' | 'NO_CAMERA' | 'NO_ORIENTATION_SENSOR'
}

interface ArPluginApi {
  open(point: ArPoint): Promise<ArResult>
}

const plugin = registerPlugin<ArPluginApi>('MarshrutyAr')

/** AR есть только в APK, собранном вместе с модулем `mobile/ar`. */
export function isArAvailable(): boolean {
  return Capacitor.isNativePlatform() && Capacitor.isPluginAvailable('MarshrutyAr')
}

export function openAr(point: ArPoint): Promise<ArResult> {
  return plugin.open(point)
}

/** Сколько держится одна строка субтитров, мс: прочитать на ходу и не спешить. */
const LINE_MS = 6000

/**
 * Рассказ точки — в субтитры по предложениям. Озвучки пока нет: модуль всё
 * равно показывает текст, а на улице его чаще читают, чем слушают.
 */
export function buildSubtitles(story: string): ArSubtitle[] {
  const sentences = story
    .split(/(?<=[.!?…])\s+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean)
  return sentences.map((text, index) => ({ fromMs: index * LINE_MS, toMs: (index + 1) * LINE_MS, text }))
}
