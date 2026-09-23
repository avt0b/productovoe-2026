import { onScopeDispose, ref, type Ref } from 'vue'

import { errorText, plural } from '@/core/format'
import type { UserPosition } from '@/core/geo'

import { sendBump, type BumpResult } from './api'
import { useShake, type ShakeOptions } from './useShake'

/** Что показать под «тряской»: подсказку, ошибку или успех. */
export interface BumpNotice {
  tone: 'info' | 'error' | 'success'
  text: string
}

/** Полноэкранное «Вы вместе!» после совпавшего бампа. */
export interface BumpCelebration {
  title: string
  subtitle: string
}

export interface BumpOptions {
  excursionId: () => string
  /** Краевед встречает участников, участник — краеведа: от этого зависят тексты. */
  isGuide: () => boolean
  /** Сбор открыт — без этого сервер встряску не примет. */
  isOpen: () => boolean
  /** Где человек. Без GPS сервер не поймёт, что двое стоят рядом. */
  position: Ref<UserPosition | null>
  /** Встряска ушла — например, перечитать, сколько человек уже в группе. */
  afterBump?: (result: BumpResult) => void | Promise<void>
  shake?: ShakeOptions
}

/** Дольше этого «тряхнули N мс назад» не шлём: такая встряска уже ни с чем не совпадёт. */
const MAX_SHAKE_AGE_MS = 5000

/**
 * Бамп целиком: датчик тряски → место → встряска на сервер → результат.
 *
 * Экран отдаёт, чья это экскурсия и где человек, и показывает `notice`,
 * `together` и индикатор силы тряски. Всё про сам бамп — пороги датчика,
 * тексты, анимация — живёт здесь, в `features/bump`, и правится здесь же.
 */
export function useBump(options: BumpOptions) {
  const sending = ref(false)
  const notice = ref<BumpNotice | null>(null)
  const together = ref<BumpCelebration | null>(null)

  const sensor = useShake((shakenAt) => void onShake(shakenAt), options.shake)

  async function onShake(shakenAt: number): Promise<void> {
    if (sending.value) return
    if (!options.isOpen()) {
      notice.value = {
        tone: 'info',
        text: options.isGuide() ? 'Сначала откройте сбор' : 'Краевед ещё не открыл сбор — подождите',
      }
      return
    }
    const fix = options.position.value
    if (!fix) {
      notice.value = { tone: 'info', text: 'Ждём GPS — встряхните ещё раз через пару секунд' }
      return
    }

    sending.value = true
    notice.value = { tone: 'info', text: options.isGuide() ? 'Ищем, кто трясёт вместе с вами…' : 'Ищем краеведа…' }
    try {
      const shakenMsAgo = Math.min(MAX_SHAKE_AGE_MS, Math.max(0, Math.round(performance.now() - shakenAt)))
      const result = await sendBump(options.excursionId(), fix, shakenMsAgo)
      showResult(result)
      await options.afterBump?.(result)
    } catch (reason) {
      notice.value = { tone: 'error', text: errorText(reason) }
    } finally {
      sending.value = false
    }
  }

  function showResult(result: BumpResult): void {
    const guide = options.isGuide()
    if (result.result === 'matched') {
      notice.value = null
      // Число «в группе» из ответа краеведу не берём: отметку ставит запрос участника,
      // и он может сохраниться на долю секунды позже. Счётчик на экране догонит опросом.
      const matched = result.matched_user_ids.length
      together.value = guide
        ? {
            title: 'Вы вместе!',
            subtitle:
              matched === 1
                ? 'Участник отмечен — он в группе'
                : `Отмечены ${matched} ${plural(matched, ['участник', 'участника', 'участников'])}`,
          }
        : { title: 'Вы вместе!', subtitle: 'Краевед отметил, что вы пришли. Хорошей экскурсии!' }
      return
    }
    if (result.result === 'already_checked_in') {
      notice.value = { tone: 'success', text: 'Вы уже в группе — трясти больше не нужно' }
      return
    }
    notice.value = {
      tone: 'info',
      text: guide
        ? 'Никто не встряхнул телефон одновременно с вами — попробуйте ещё раз вместе'
        : 'Краевед не встряхнул телефон одновременно с вами — договоритесь и попробуйте ещё раз',
    }
  }

  onScopeDispose(sensor.stop)

  return {
    /** Датчик: `start` — только из нажатия (иначе iPhone не спросит разрешение), `trigger` — кнопка «Встряхнуть». */
    sensor,
    sending,
    notice,
    together,
  }
}
