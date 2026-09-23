import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/search'

function listNeedsByStatus({ kind, status }) {
  const params = new URLSearchParams({ status })
  if (kind) params.set('kind', kind)
  return http.get(`${BASE}/needs?${params.toString()}`)
}

// GET /needs без ?status по умолчанию отдаёт только open (see needs.py) —
// сервер не умеет отдавать все статусы одним запросом, поэтому берём оба
// и сливаем, чтобы закрытые сборы не пропадали из списка бесследно, а
// показывались как завершённые.
export async function listNeeds({ kind } = {}) {
  const [open, closed] = await Promise.all([
    listNeedsByStatus({ kind, status: 'open' }),
    listNeedsByStatus({ kind, status: 'closed' }),
  ])
  return [...open, ...closed]
}

export function listSquads() {
  return http.get(`${BASE}/squads`)
}

export function donate(token, needId, { amount, comment }) {
  return http.post(`${BASE}/needs/${needId}/donations`, { amount, comment }, { token })
}
