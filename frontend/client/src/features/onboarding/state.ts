import { computed, ref } from 'vue'

/**
 * Что человек уже видел из обучения.
 *
 * Хранится в браузере, а не в профиле: обучение — свойство устройства, а не
 * человека. Зашли с чужого телефона — там своё приветствие, и это честно.
 */
const STORAGE_KEY = 'marshruty.client.onboarding'

/**
 * Версия обучения. Выросла — приветствие покажем ещё раз: значит, в приложении
 * появился раздел, о котором человек не знает. Не трогать ради правки опечатки.
 */
export const TOUR_VERSION = 1

function read(): number {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const value = raw ? (JSON.parse(raw) as { version?: unknown }).version : 0
    return typeof value === 'number' ? value : 0
  } catch {
    return 0
  }
}

const seen = ref(read())

/** Какую версию обучения человек уже закрыл. 0 — не видел ничего. */
export const seenVersion = computed(() => seen.value)

/** Приветствие ещё не показывали (или обучение с тех пор обновилось). */
export const needsWelcome = computed(() => seen.value < TOUR_VERSION)

export function markSeen(version = TOUR_VERSION): void {
  if (seen.value >= version) return
  seen.value = version
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ version }))
  } catch {
    /* приватный режим — приветствие вернётся в следующий раз, это не страшно */
  }
}

/** «Показать обучение заново» из настроек: снова здороваемся при следующем входе. */
export function forgetOnboarding(): void {
  seen.value = 0
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* см. выше */
  }
}
