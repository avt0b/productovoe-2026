import { apiRequest } from '@/core/api'
import { useSessionStore } from '@/core/session'

import * as mock from './mock'

/**
 * Рейтинг краеведов (CONTRACT 2). Общая фича трёх мест: экран рейтинга, полоска
 * в «Экскурсиях», карточка краеведа и блок в профиле. Пока бэкенда нет,
 * `VITE_MOCK_NEW_API` переключает функции на заглушку.
 */
const MOCK = import.meta.env.VITE_MOCK_NEW_API === 'true'

export type RatingPeriod = 'all' | 'month'

export interface GuideRank {
  place: number
  guide_id: string
  display_name: string
  avatar_url: string | null
  city: string
  is_verified: boolean
  average: number
  count: number
  score: number
  excursions_led: number
  last_rated_at: string | null
  is_me: boolean
}

export interface GuideLeaderboard {
  period: RatingPeriod
  global_average: number
  prior_weight: number
  total: number
  items: GuideRank[]
}

export interface GuideReview {
  id: string
  excursion_id: string
  guide_id: string
  rater_id: string
  rating: number
  comment: string
  created_at: string
  rater_name: string
  rater_avatar_url: string | null
  excursion_title: string
}

export interface GuideCard {
  guide_id: string
  average: number
  count: number
  recent: GuideReview[]
  score: number | null
  place: number | null
  total_ranked: number
  excursions_led: number
  distribution: Record<'1' | '2' | '3' | '4' | '5', number>
  profile: {
    display_name: string
    avatar_url: string | null
    city: string
    role: string
    is_verified: boolean
  } | null
}

/** Ближайшая экскурсия краеведа — только то, что нужно карточке. */
export interface GuideExcursion {
  id: string
  title: string
  place_name: string
  starts_at: string
  status: string
}

/** Ответ /excursions шире — берём только нужные поля. */
interface RawExcursion {
  id: string
  title: string
  place_name: string
  starts_at: string
  status: string
}

export function fetchLeaderboard(
  period: RatingPeriod,
  { limit = 50, offset = 0 }: { limit?: number; offset?: number } = {},
): Promise<GuideLeaderboard> {
  if (MOCK) return mock.fetchLeaderboard(period, { limit, offset })
  // С токеном — чтобы у своей строки был is_me; без аккаунта ручка публичная.
  const auth = useSessionStore().hasAccount
  return apiRequest('GET', 'hq', '/guides/rating', { query: { period, limit, offset }, auth })
}

export function fetchGuideCard(guideId: string): Promise<GuideCard> {
  if (MOCK) return mock.fetchGuideCard(guideId)
  return apiRequest('GET', 'hq', `/guides/${encodeURIComponent(guideId)}/rating`, {})
}

export async function fetchGuideExcursions(guideId: string): Promise<GuideExcursion[]> {
  if (MOCK) return mock.fetchGuideExcursions(guideId)
  const list = await apiRequest<RawExcursion[]>('GET', 'hq', '/excursions', {
    query: { guide_id: guideId, upcoming_only: true },
  })
  return list.map((e) => ({ id: e.id, title: e.title, place_name: e.place_name, starts_at: e.starts_at, status: e.status }))
}
