import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/archive/entries'

// Карточки бойцов — та же сущность «народного архива» (archive_service),
// что и остальная «Живая память», просто отфильтрованная по
// kind=soldier_card и со своей витриной поиска/фильтров, как в «Книге
// памяти». Публичная лента отдаёт только verified-записи (см.
// EntryService.search_public), q — полнотекстовый поиск по названию/тексту.
export function listSoldierCards({ q } = {}) {
  const params = new URLSearchParams({ kind: 'soldier_card', limit: '200' })
  if (q) params.set('q', q)
  return http.get(`${BASE}?${params}`)
}
