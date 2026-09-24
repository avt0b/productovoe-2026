import { ref } from 'vue'

/**
 * Отложенные точки маршрута.
 *
 * Хранятся в браузере, а не в сервисе: своей ручки для закладок у
 * `route_service` нет, а кнопка-звёздочка, которая забывает выбор при
 * перезагрузке, — обманка. Появится ручка — переедут туда, экран не изменится.
 */
const STORAGE_KEY = 'marshruty.route-point.bookmarks'

function read(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed: unknown = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed.filter((id): id is string => typeof id === 'string') : []
  } catch {
    // Приватный режим или выключенное хранилище — живём без закладок.
    return []
  }
}

const ids = ref<string[]>(read())

function write(): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ids.value))
  } catch {
    // Не записалось — закладка останется до перезагрузки, ломать экран из-за этого незачем.
  }
}

export function useBookmarks() {
  return {
    has: (pointId: string): boolean => ids.value.includes(pointId),
    toggle: (pointId: string): void => {
      ids.value = ids.value.includes(pointId) ? ids.value.filter((id) => id !== pointId) : [...ids.value, pointId]
      write()
    },
  }
}
