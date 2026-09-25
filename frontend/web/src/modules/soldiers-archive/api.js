import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/archive/entries'

// Карточки бойцов — та же сущность «народного архива», что и остальная
// «Живая память», просто отфильтрованная по kind=soldier_card. Публичная
// лента отдаёт только подтверждённые записи.
//
// Карточек десятки тысяч (Книга памяти по выгрузке ОБД «Мемориал»), поэтому
// целиком на страницу их не тянем: листаем по алфавиту страницами, поиск (q)
// и буква алфавита (prefix) считаются на сервере, счётчики шапки — отдельной
// сводкой.
export const PAGE_SIZE = 100

export function listSoldierCards({ q, letter, offset = 0 } = {}) {
  const params = new URLSearchParams({
    kind: 'soldier_card',
    sort: 'title',
    limit: String(PAGE_SIZE),
    offset: String(offset),
  })
  if (q) params.set('q', q)
  if (letter) params.set('prefix', letter)
  return http.get(`${BASE}?${params}`)
}

export function soldierCardsSummary() {
  return http.get(`${BASE}/summary?kind=soldier_card`)
}
