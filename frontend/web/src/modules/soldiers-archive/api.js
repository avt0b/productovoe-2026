import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/archive/entries'

// Карточки бойцов — та же сущность «народного архива» (archive_service),
// что и остальная «Живая память», просто отфильтрованная по
// kind=soldier_card и со своей витриной поиска/фильтров, как в «Книге
// памяти». Публичная лента отдаёт только verified-записи (см.
// EntryService.search_public), q — полнотекстовый поиск по названию/тексту.
// limit жёстко ограничен 200 на бэке (Query(le=200)) — архив уже больше
// одной страницы, поэтому листаем через offset, пока не придёт неполная
// страница.
export async function listSoldierCards({ q } = {}) {
  const pageSize = 200
  let offset = 0
  const all = []
  for (;;) {
    const params = new URLSearchParams({ kind: 'soldier_card', limit: String(pageSize), offset: String(offset) })
    if (q) params.set('q', q)
     
    const page = await http.get(`${BASE}?${params}`)
    all.push(...page)
    if (page.length < pageSize) break
    offset += pageSize
  }
  return all
}
