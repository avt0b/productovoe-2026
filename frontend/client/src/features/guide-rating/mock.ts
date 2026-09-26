import { withLatency } from '@/core/mock'
import { useSessionStore } from '@/core/session'

import type { GuideCard, GuideExcursion, GuideLeaderboard, GuideRank, GuideReview, RatingPeriod } from './api'

/**
 * Заглушка рейтинга: восемь краеведов с разным числом оценок — чтобы было
 * видно, что одна пятёрка стоит ниже сорока оценок по 4,8. Данные и карточка
 * собраны по CONTRACT 2.3–2.5.
 */
const PRIOR_WEIGHT = 5

interface Seed {
  guide_id: string
  display_name: string
  city: string
  is_verified: boolean
  average: number
  count: number
  excursions_led: number
  daysAgo: number
}

const SEEDS: Seed[] = [
  { guide_id: 'g-anna', display_name: 'Анна Сергеевна', city: 'Орёл', is_verified: true, average: 4.9, count: 23, excursions_led: 12, daysAgo: 1 },
  { guide_id: 'g-petr', display_name: 'Пётр Ильич', city: 'Орёл', is_verified: true, average: 4.8, count: 40, excursions_led: 20, daysAgo: 2 },
  { guide_id: 'g-maria', display_name: 'Мария Котова', city: 'Мценск', is_verified: false, average: 5.0, count: 5, excursions_led: 3, daysAgo: 5 },
  { guide_id: 'g-olga', display_name: 'Ольга Белых', city: 'Ливны', is_verified: false, average: 4.7, count: 15, excursions_led: 8, daysAgo: 3 },
  { guide_id: 'g-elena', display_name: 'Елена Рощина', city: 'Орёл', is_verified: true, average: 4.85, count: 12, excursions_led: 7, daysAgo: 4 },
  { guide_id: 'g-irina', display_name: 'Ирина Дьякова', city: 'Болхов', is_verified: false, average: 4.5, count: 30, excursions_led: 14, daysAgo: 6 },
  { guide_id: 'g-sergey', display_name: 'Сергей Волков', city: 'Орёл', is_verified: false, average: 4.6, count: 8, excursions_led: 5, daysAgo: 8 },
  { guide_id: 'g-dmitry', display_name: 'Дмитрий Орлов', city: 'Орёл', is_verified: false, average: 5.0, count: 3, excursions_led: 2, daysAgo: 12 },
]

const round2 = (n: number): number => Math.round(n * 100) / 100
const iso = (daysAgo: number): string => new Date(Date.now() - daysAgo * 86_400_000).toISOString()

/** Для периода «месяц» оценок меньше — показываем, что таблица другая. */
function forPeriod(period: RatingPeriod): Seed[] {
  if (period === 'all') return SEEDS
  return SEEDS.filter((s) => s.count >= 8).map((s) => ({ ...s, count: Math.max(1, Math.round(s.count / 2)) }))
}

function globalAverage(seeds: Seed[]): number {
  const total = seeds.reduce((n, s) => n + s.count, 0)
  if (total === 0) return 0
  return seeds.reduce((n, s) => n + s.average * s.count, 0) / total
}

function score(seed: Seed, m: number): number {
  return (PRIOR_WEIGHT * m + seed.average * seed.count) / (PRIOR_WEIGHT + seed.count)
}

export function fetchLeaderboard(
  period: RatingPeriod,
  { limit = 50, offset = 0 }: { limit?: number; offset?: number } = {},
): Promise<GuideLeaderboard> {
  const seeds = forPeriod(period)
  const m = globalAverage(seeds)
  const myId = useSessionStore().user?.id
  const ranked = seeds
    .map((s) => ({ seed: s, score: score(s, m) }))
    .sort((a, b) => b.score - a.score || b.seed.count - a.seed.count || a.seed.guide_id.localeCompare(b.seed.guide_id))
  const items: GuideRank[] = ranked.map(({ seed, score: sc }, i) => ({
    place: i + 1,
    guide_id: seed.guide_id,
    display_name: seed.display_name,
    avatar_url: null,
    city: seed.city,
    is_verified: seed.is_verified,
    average: round2(seed.average),
    count: seed.count,
    score: Math.round(sc * 1000) / 1000,
    excursions_led: seed.excursions_led,
    last_rated_at: iso(seed.daysAgo),
    // Своим отметим второго — чтобы в демо было видно подсветку «Это вы».
    is_me: myId === seed.guide_id || (!!myId && seed.guide_id === 'g-petr'),
  }))
  return withLatency({
    period,
    global_average: round2(m),
    prior_weight: PRIOR_WEIGHT,
    total: items.length,
    items: items.slice(offset, offset + limit),
  })
}

const COMMENTS = [
  'Рассказывала так, что дети слушали час',
  'Очень живо и по делу, спасибо!',
  'Много редких деталей, которых нет в учебниках',
  'Маршрут продуман, ни разу не заскучали',
  '',
]

/** Распределение оценок под среднее и число: почти все пятёрки, немного ниже. */
function distribution(average: number, count: number): Record<'1' | '2' | '3' | '4' | '5', number> {
  const dist = { '1': 0, '2': 0, '3': 0, '4': 0, '5': 0 } as Record<'1' | '2' | '3' | '4' | '5', number>
  for (let i = 0; i < count; i += 1) {
    const r = Math.round(average + (Math.random() - 0.5) * 0.8)
    const clamped = Math.min(5, Math.max(3, r))
    dist[String(clamped) as '3' | '4' | '5'] += 1
  }
  return dist
}

function reviews(seed: Seed): GuideReview[] {
  const n = Math.min(20, seed.count)
  return Array.from({ length: n }, (_, i) => ({
    id: `${seed.guide_id}-rev-${i}`,
    excursion_id: `${seed.guide_id}-exc-${i % 3}`,
    guide_id: seed.guide_id,
    rater_id: `rater-${i}`,
    rating: Math.min(5, Math.max(4, Math.round(seed.average))),
    comment: COMMENTS[i % COMMENTS.length],
    created_at: iso(seed.daysAgo + i),
    rater_name: ['Ирина', 'Олег', 'Наталья', 'Павел', 'Светлана'][i % 5],
    rater_avatar_url: null,
    excursion_title: 'Мценск: первогвардейцы и освобождение города',
  }))
}

export function fetchGuideCard(guideId: string): Promise<GuideCard> {
  const m = globalAverage(SEEDS)
  const ranked = SEEDS.map((s) => ({ s, sc: score(s, m) })).sort((a, b) => b.sc - a.sc)
  // Неизвестный id (напр. свой профиль в демо) → показываем карточку лидера с этим id.
  const idx = Math.max(0, ranked.findIndex((r) => r.s.guide_id === guideId))
  const { s: seed } = ranked[idx]
  const place = idx + 1
  return withLatency({
    guide_id: guideId,
    average: round2(seed.average),
    count: seed.count,
    recent: reviews(seed),
    score: Math.round(ranked[idx].sc * 1000) / 1000,
    place,
    total_ranked: SEEDS.length,
    excursions_led: seed.excursions_led,
    distribution: distribution(seed.average, seed.count),
    profile: {
      display_name: seed.display_name,
      avatar_url: null,
      city: seed.city,
      role: 'local_historian',
      is_verified: seed.is_verified,
    },
  })
}

export function fetchGuideExcursions(_guideId: string): Promise<GuideExcursion[]> {
  return withLatency([
    { id: 'exc-1', title: 'Мценск: первогвардейцы и освобождение города', place_name: 'Мценск', starts_at: iso(-3), status: 'scheduled' },
    { id: 'exc-2', title: 'Орёл: улицы освободителей', place_name: 'Орёл', starts_at: iso(-7), status: 'scheduled' },
  ])
}
