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

/** Метки на карте — как в кейсе: красные ждут проверки, зелёные подтверждены или отработаны. */
export const STATUS_STYLE: Record<FindStatus, { icon: string; tone: GeoTone }> = {
  found: { icon: 'person_search', tone: 'primary' },
  confirmed: { icon: 'verified', tone: 'secondary' },
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

/** Сменить стадию — только модератор. */
export function setPointStatus(pointId: string, status: FindStatus): Promise<LastStandPoint> {
  return apiRequest('PATCH', 'map', `/last-stand/${encodeURIComponent(pointId)}/status`, {
    body: { status: TO_SERVICE[status] },
    auth: true,
  })
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
