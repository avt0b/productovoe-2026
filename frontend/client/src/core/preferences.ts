import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const STORAGE_KEY = 'marshruty.client.preferences'

interface StoredPreferences {
  familyMode: boolean
}

const DEFAULTS: StoredPreferences = {
  // В макете входа переключатель включён: приложение прежде всего для семей.
  familyMode: true,
}

function read(): StoredPreferences {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? { ...DEFAULTS, ...(JSON.parse(raw) as Partial<StoredPreferences>) } : DEFAULTS
  } catch {
    return DEFAULTS
  }
}

function write(value: StoredPreferences): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value))
  } catch {
    /* приватный режим — настройка проживёт до закрытия вкладки */
  }
}

/**
 * Настройки, которые меняют в нескольких окнах.
 *
 * Семейный режим переключают и на экране входа, и в профиле. Держать его в
 * одном из модулей значило бы заставить второй импортировать первый — а модули
 * друг о друге не знают. Поэтому он живёт в ядре.
 */
export const usePreferencesStore = defineStore('preferences', () => {
  const stored = read()
  /** Семейный и детский режим: адаптированные квесты, мягкая подача тяжёлых деталей. */
  const familyMode = ref(stored.familyMode)

  watch(familyMode, (value) => write({ familyMode: value }))

  return { familyMode }
})
