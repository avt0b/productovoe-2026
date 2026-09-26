import { ApiError } from '@/core/api'
import { distanceKm } from '@/core/geo'
import { withLatency } from '@/core/mock'

import type { LostAlert, LostPosition, LostWatcher, RaiseLostBody } from './api'

/**
 * Заглушка тревоги: весь сценарий «Я потерялся» проходится в браузере без
 * бэкенда. Состояние — в памяти модуля; переключается `VITE_MOCK_LOST_ROLE`.
 * Данные собраны из примеров CONTRACT 1.3, чтобы переход на живой бэкенд был
 * просто выключением флага.
 */
const ROLE = import.meta.env.VITE_MOCK_LOST_ROLE === 'lost' ? 'lost' : 'watcher'

const EXCURSION_ID = '9b2e41aa-0c7e-4f5e-8f55-6c1d2a3b4c5d'
const EXCURSION_TITLE = 'Мценск: первогвардейцы и освобождение города'
const ME_ID = '0a1b2c3d-0000-4a4a-9b9b-000000000000'
const MASHA_ID = '0a1b2c3d-1111-4a4a-9b9b-000000000001'
const MAMA_ID = '0a1b2c3d-2222-4a4a-9b9b-000000000002'
const GUIDE_ID = '0a1b2c3d-3333-4a4a-9b9b-000000000003'

/** Рядом с Орлом: у потерявшегося и у ищущих точки в паре сотен метров друг от друга. */
const LOST_START = { lat: 52.9700, lon: 36.0665 }
const MAMA_START = { lat: 52.9686, lon: 36.0694 }

let alerts: LostAlert[] = []
/** Момент создания каждой тревоги — чтобы через ~20 с «откликнуть» маму. */
const createdMs = new Map<string, number>()
let seeded = false
let counter = 0

const iso = (ms: number): string => new Date(ms).toISOString()

function pos(lat: number, lon: number, accuracy: number, at: number): LostPosition {
  return { lat, lon, accuracy_m: accuracy, updated_at: iso(at) }
}

function distanceM(a: { lat: number; lon: number } | null, b: { lat: number; lon: number } | null): number | null {
  if (!a || !b) return null
  return Math.round(distanceKm(a, b) * 1000)
}

/** Пересчитать расстояния и порядок ищущих: откликнувшиеся, потом ближние, null в конце. */
function reorder(alert: LostAlert): void {
  const lost = alert.lost.position
  for (const w of alert.watchers) w.distance_m = distanceM(w.position, lost)
  alert.watchers.sort((a, b) => {
    if (a.responding !== b.responding) return a.responding ? -1 : 1
    if (a.distance_m === null) return b.distance_m === null ? 0 : 1
    if (b.distance_m === null) return -1
    return a.distance_m - b.distance_m
  })
}

function makeAlert(role: 'watcher' | 'lost', body: RaiseLostBody = {}): LostAlert {
  counter += 1
  const id = `alert-${counter}-${Math.random().toString(36).slice(2, 8)}`
  const at = Date.now()
  // Точка потерявшегося: своя из body (я потерялся) или дефолтная (за меня).
  const lostPos =
    role === 'lost' && typeof body.lat === 'number' && typeof body.lon === 'number'
      ? pos(body.lat, body.lon, body.accuracy_m ?? 12, at)
      : pos(LOST_START.lat, LOST_START.lon, 15, at)

  const mama: LostWatcher = {
    user_id: MAMA_ID,
    display_name: 'Мама',
    avatar_url: null,
    relation: 'family',
    is_me: role === 'watcher',
    responding: false,
    responded_at: null,
    position: pos(MAMA_START.lat, MAMA_START.lon, 8, at),
    distance_m: null,
  }
  const guide: LostWatcher = {
    user_id: GUIDE_ID,
    display_name: 'Анна Сергеевна',
    avatar_url: null,
    relation: 'guide',
    is_me: false,
    responding: false,
    responded_at: null,
    position: null,
    distance_m: null,
  }

  const alert: LostAlert = {
    id,
    excursion_id: EXCURSION_ID,
    excursion_title: EXCURSION_TITLE,
    status: 'active',
    kind: 'self',
    my_role: role,
    message: (body.message ?? '').trim(),
    lost: {
      user_id: role === 'lost' ? ME_ID : MASHA_ID,
      display_name: role === 'lost' ? 'Вы' : 'Маша',
      avatar_url: null,
      is_me: role === 'lost',
      position: lostPos,
    },
    raised_by: { user_id: role === 'lost' ? ME_ID : MASHA_ID, display_name: role === 'lost' ? 'Вы' : 'Маша' },
    watchers: [mama, guide],
    created_at: iso(at),
    resolved_at: null,
    resolved_by: null,
  }
  reorder(alert)
  createdMs.set(id, at)
  return alert
}

function ensureSeed(): void {
  if (seeded) return
  seeded = true
  // Я ищущий: тревога уже висит, экран должен открыться сам.
  if (ROLE === 'watcher') alerts = [makeAlert('watcher')]
}

/** Слегка сдвинуть потерявшегося (±5 м) и подтянуть откликнувшихся к нему (~15 м). */
function tick(alert: LostAlert): void {
  if (alert.status !== 'active') return
  const now = Date.now()
  const lost = alert.lost.position
  if (lost) {
    lost.lat += (Math.random() - 0.5) * 0.0001 // ~±5 м по широте
    lost.lon += (Math.random() - 0.5) * 0.00015
    lost.updated_at = iso(now)
  }
  // Через ~20 с после создания заглушка «откликает» маму — у потерявшегося
  // появится «Мама идёт к вам».
  const created = createdMs.get(alert.id) ?? now
  if (alert.my_role === 'lost' && now - created > 20_000) {
    const mama = alert.watchers.find((w) => w.user_id === MAMA_ID)
    if (mama && !mama.responding) {
      mama.responding = true
      mama.responded_at = iso(now)
    }
  }
  for (const w of alert.watchers) {
    if (w.responding && w.position && lost) {
      // 15 м ближе вдоль прямой к потерявшемуся.
      const total = distanceKm(w.position, lost) * 1000
      if (total > 20) {
        const step = 15 / total
        w.position.lat += (lost.lat - w.position.lat) * step
        w.position.lon += (lost.lon - w.position.lon) * step
        w.position.updated_at = iso(now)
      }
    }
  }
  reorder(alert)
}

function find(alertId: string): LostAlert {
  const alert = alerts.find((a) => a.id === alertId)
  if (!alert) throw new ApiError(404, 'Поиск не найден')
  return alert
}

export function raiseLost(_excursionId: string, body: RaiseLostBody): Promise<LostAlert> {
  ensureSeed()
  // Дать увидеть ошибку из detail: слово «ошибка» в подписи роняет запрос.
  if ((body.message ?? '').toLowerCase().includes('ошибка')) {
    return Promise.reject(new ApiError(409, 'Потеряться можно только во время прогулки группы'))
  }
  // Одна открытая тревога на человека: я уже потерян — вернуть её (код 200 у бэкенда).
  const mineOpen = alerts.find((a) => a.my_role === 'lost' && a.status === 'active')
  if (mineOpen && !body.lost_user_id) return withLatency(mineOpen)
  const alert = makeAlert('lost', body)
  alerts = [alert, ...alerts]
  return withLatency(alert)
}

export function fetchActiveAlerts(): Promise<LostAlert[]> {
  ensureSeed()
  alerts.forEach(tick)
  return withLatency(alerts.filter((a) => a.status === 'active'))
}

export function fetchAlert(alertId: string): Promise<LostAlert> {
  ensureSeed()
  const alert = find(alertId)
  tick(alert)
  return withLatency(alert)
}

export function respondAlert(alertId: string): Promise<LostAlert> {
  const alert = find(alertId)
  if (alert.status !== 'active') return Promise.reject(new ApiError(409, 'Поиск уже закрыт'))
  const me = alert.watchers.find((w) => w.is_me)
  if (me && !me.responding) {
    me.responding = true
    me.responded_at = iso(Date.now())
    reorder(alert)
  }
  return withLatency(alert)
}

export function resolveAlert(alertId: string): Promise<LostAlert> {
  const alert = find(alertId)
  if (alert.status === 'active') {
    alert.status = 'found'
    alert.resolved_at = iso(Date.now())
    alert.resolved_by = { user_id: ME_ID, display_name: alert.my_role === 'lost' ? 'Вы' : 'Мама' }
  }
  return withLatency(alert)
}

export function cancelAlert(alertId: string): Promise<LostAlert> {
  const alert = find(alertId)
  if (alert.status === 'active') {
    alert.status = 'cancelled'
    alert.resolved_at = iso(Date.now())
    alert.resolved_by = { user_id: ME_ID, display_name: alert.my_role === 'lost' ? 'Вы' : 'Мама' }
  }
  return withLatency(alert)
}

export function reportMyPosition(
  _excursionId: string,
  _position: { lat: number; lon: number; accuracy_m: number | null },
): Promise<void> {
  // Заглушке чужая точка не нужна: движение людей она считает сама в tick().
  return withLatency(undefined)
}
