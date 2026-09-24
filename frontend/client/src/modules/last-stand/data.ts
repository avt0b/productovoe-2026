import { apiRequest, type DataSource } from '@/core/api'
import { formatCoordinates, type GeoTone, type LatLon } from '@/core/geo'
import { listLastStand, type LastStandPoint, type LastStandStatus } from '@/core/services/map'

/**
 * Данные окна «Последний бой» — места гибели бойцов из `map_service`
 * (`/last-stand`): добавить место, сменить статус (модератор). «Дополнить
 * данными» — запись народного архива (`archive_service`) с координатами места.
 *
 * Если сервис не ответил, приходит демо-набор Орловщины из
 * `core/services/demoOrel.ts`, а экран показывает плашку «демо-данные».
 */

/** Стадия находки: обнаружено и проверяется → подтверждено архивом → останки подняты. */
export type FindStatus = 'found' | 'confirmed' | 'raised'

export const STATUS_LABELS: Record<FindStatus, string> = {
  found: 'Обнаружено (проверка)',
  confirmed: 'Подтверждено архивом',
  raised: 'Останки подняты',
}

/**
 * Метки на карте. Кейс просит красные для непроверенных и зелёные для
 * отработанных; дизайн-контракт добавляет третью роль — «подтверждено» везде
 * в приложении латунное. Так три стадии различимы, а не две зелёные подряд.
 */
export const STATUS_STYLE: Record<FindStatus, { icon: string; tone: GeoTone }> = {
  found: { icon: 'person_search', tone: 'primary' },
  confirmed: { icon: 'verified', tone: 'tertiary' },
  raised: { icon: 'local_florist', tone: 'secondary' },
}

const FROM_SERVICE: Record<LastStandStatus, FindStatus> = {
  discovered: 'found',
  archive_confirmed: 'confirmed',
  remains_raised: 'raised',
}

export const TO_SERVICE: Record<FindStatus, LastStandStatus> = {
  found: 'discovered',
  confirmed: 'archive_confirmed',
  raised: 'remains_raised',
}

/** Подпись, когда дата гибели неизвестна. */
const NO_DATE = 'Дата гибели не установлена'

export interface FindRecord extends LatLon {
  id: string
  status: FindStatus
  stage: string
  title: string
  unit: string
  period: string
  coordinates: string
  source: string
  evidence: string
  /**
   * Поля сервиса как есть. В карточке они причёсаны («Неизвестный боец»,
   * «Обстоятельства уточняются»), а правит автор именно исходные — иначе в
   * форму попали бы наши подписи вместо пустых граф.
   */
  raw: {
    created_by: string
    soldier_name: string
    unit: string
    circumstances: string
    date_text: string
    source: string
  }
}

export interface LastStandOverview {
  records: FindRecord[]
  source: DataSource
}

export async function fetchLastStand(): Promise<LastStandOverview> {
  const { data, source } = await listLastStand()
  return { records: data.map(toRecord), source }
}

function toRecord(point: LastStandPoint): FindRecord {
  const status = FROM_SERVICE[point.status]
  return {
    id: point.id,
    status,
    stage: STATUS_LABELS[status],
    // Имя бойца часто неизвестно — это нормально для «Последнего боя», а не пропуск в данных.
    title: point.soldier_name || 'Неизвестный боец',
    unit: point.unit,
    period: point.date_text || NO_DATE,
    coordinates: formatCoordinates(point),
    source: point.source || 'Источник не указан',
    evidence: point.circumstances || 'Обстоятельства гибели уточняются',
    lat: point.lat,
    lon: point.lon,
    raw: {
      created_by: point.created_by,
      soldier_name: point.soldier_name,
      unit: point.unit,
      circumstances: point.circumstances,
      date_text: point.date_text,
      source: point.source,
    },
  }
}

export interface PointDraft extends LatLon {
  soldier_name: string
  unit: string
  circumstances: string
  date_text: string
  source: string
}

/** Новое место — поисковику, краеведу, наставнику, модератору. Появляется со статусом «Обнаружено». */
export function createPoint(draft: PointDraft): Promise<LastStandPoint> {
  return apiRequest('POST', 'map', '/last-stand', { body: draft, auth: true })
}

/**
 * Поправить место — автор или модератор (`_ensure_can_edit` в map_service).
 * После экспедиции уточняют обстоятельства, часть и координаты.
 */
export function updatePoint(pointId: string, patch: Partial<PointDraft>): Promise<LastStandPoint> {
  return apiRequest('PATCH', 'map', `/last-stand/${encodeURIComponent(pointId)}`, { body: patch, auth: true })
}

/** Сменить стадию — только модератор. */
export function setPointStatus(pointId: string, status: FindStatus): Promise<LastStandPoint> {
  return apiRequest('PATCH', 'map', `/last-stand/${encodeURIComponent(pointId)}/status`, {
    body: { status: TO_SERVICE[status] },
    auth: true,
  })
}

// --- источник сведений ---

/**
 * Откуда известно о месте. Кейс требует привязки к краеведческим источникам:
 * для Орловщины это тома «Книги Памяти» (т. 1–13) и сборник «Выстояли и
 * победили!», а ещё донесения «Памяти народа» и рассказы жителей.
 *
 * Сервис хранит источник одной строкой, поэтому вид и реквизиты собираются в
 * фразу, по которой краевед найдёт документ: «Книга Памяти Орловской области,
 * т. 5, с. 214». Свободная строка «Источник» давала «кн. пам.» и «спросить у
 * деда» — проверить такое нельзя.
 */
export type SourceKind = 'memory_book' | 'collection' | 'people_memory' | 'witness' | 'expedition' | 'other'

export const SOURCE_KINDS: { value: SourceKind; title: string; icon: string }[] = [
  { value: 'memory_book', title: 'Книга Памяти', icon: 'menu_book' },
  { value: 'collection', title: '«Выстояли и победили!»', icon: 'auto_stories' },
  { value: 'people_memory', title: '«Память народа»', icon: 'travel_explore' },
  { value: 'witness', title: 'Рассказ жителя', icon: 'record_voice_over' },
  { value: 'expedition', title: 'Отчёт экспедиции', icon: 'hiking' },
  { value: 'other', title: 'Другое', icon: 'description' },
]

/** Томов «Книги Памяти» Орловской области — тринадцать, 1995–2015. */
export const MEMORY_BOOK_VOLUMES = 13

export interface SourceDraft {
  kind: SourceKind
  /** Том «Книги Памяти». */
  volume: number | null
  /** Страница — у книги и у сборника. */
  page: number | null
  /** Номер донесения или ссылка в «Памяти народа». */
  reference: string
  /** Кто рассказал и откуда он — у рассказа жителя; отряд и год — у экспедиции. */
  who: string
  /** Свободный текст — у «Другого» и как уточнение к любому виду. */
  note: string
}

export function emptySource(): SourceDraft {
  return { kind: 'memory_book', volume: null, page: null, reference: '', who: '', note: '' }
}

/** Фраза для поля `source`. Пустая, если реквизитов нет, — такой источник не засчитываем. */
export function formatSource(draft: SourceDraft): string {
  const note = draft.note.trim()
  const parts: string[] = []
  switch (draft.kind) {
    case 'memory_book':
      if (!draft.volume) return ''
      parts.push(`Книга Памяти Орловской области, т. ${draft.volume}`)
      if (draft.page) parts.push(`с. ${draft.page}`)
      break
    case 'collection':
      parts.push('Сборник «Выстояли и победили! Орловская область в годы Великой Отечественной войны»')
      if (draft.page) parts.push(`с. ${draft.page}`)
      break
    case 'people_memory':
      if (!draft.reference.trim()) return ''
      parts.push(`«Память народа»: ${draft.reference.trim()}`)
      break
    case 'witness':
      if (!draft.who.trim()) return ''
      parts.push(`Рассказ жителя: ${draft.who.trim()}`)
      break
    case 'expedition':
      if (!draft.who.trim()) return ''
      parts.push(`Отчёт экспедиции: ${draft.who.trim()}`)
      break
    case 'other':
      return note
  }
  if (note) parts.push(note)
  return parts.join(', ')
}

/** Значок источника в карточке — по тому, с чего начинается фраза. */
export function sourceIcon(source: string): string {
  if (source.startsWith('Книга Памяти')) return 'menu_book'
  if (source.startsWith('Сборник')) return 'auto_stories'
  if (source.startsWith('«Память народа»')) return 'travel_explore'
  if (source.startsWith('Рассказ жителя')) return 'record_voice_over'
  if (source.startsWith('Отчёт экспедиции')) return 'hiking'
  return 'description'
}

// --- подписка на район ---

/**
 * Кому сообщать о новых местах: `map_service` при каждой новой точке зовёт
 * `user_service`, а тот шлёт «в N км от вас обнаружено место гибели» всем,
 * у кого точка попала в радиус от их «дома». Подписка — это поля профиля.
 */
export interface SearchSubscription {
  subscribed: boolean
  radiusKm: number
  home: LatLon | null
}

/** Радиусы, которые предлагаем: пешком, по району, по области. */
export const RADIUS_OPTIONS_KM = [5, 20, 50] as const

interface ProfileSubscriptionFields {
  subscribed_to_search: boolean
  alert_radius_km: number
  home_lat: number | null
  home_lon: number | null
}

export async function fetchSubscription(): Promise<SearchSubscription> {
  const profile = await apiRequest<ProfileSubscriptionFields>('GET', 'users', '/profiles/me', { auth: true })
  return {
    subscribed: profile.subscribed_to_search,
    radiusKm: profile.alert_radius_km,
    home: profile.home_lat !== null && profile.home_lon !== null ? { lat: profile.home_lat, lon: profile.home_lon } : null,
  }
}

export async function saveSubscription(next: SearchSubscription): Promise<SearchSubscription> {
  await apiRequest('PUT', 'users', '/profiles/me', {
    body: {
      subscribed_to_search: next.subscribed,
      alert_radius_km: next.radiusKm,
      ...(next.home ? { home_lat: next.home.lat, home_lon: next.home.lon } : {}),
    },
    auth: true,
  })
  return next
}

/**
 * Окружность вокруг точки для карты. Проп `circles` у `GeoMap` добавляет
 * сторона A; форма — как у меток: id, координаты, радиус в метрах и роль
 * цвета. Тип держим здесь, пока его нет в `core/geo`.
 */
export interface MapCircle extends LatLon {
  id: string
  radiusMeters: number
  tone: GeoTone
}

/**
 * «Дополнить данными» — запись народного архива с координатами места: краевед
 * проверит её и подтвердит, как любую другую.
 */
export function addEvidence(record: FindRecord, title: string, body: string, mediaUrl: string): Promise<unknown> {
  return apiRequest('POST', 'archive', '/entries', {
    body: {
      kind: 'event',
      title,
      body,
      lat: record.lat,
      lon: record.lon,
      date_text: record.period === NO_DATE ? '' : record.period,
      media_url: mediaUrl || null,
    },
    auth: true,
  })
}
