import { apiRequest, type DataSource } from '@/core/api'
import { listPoi, type PoiKind } from '@/core/services/map'

/**
 * Данные окна «Место у метки» — куда ведёт NFC-чип на табличке у памятника.
 *
 * Факты — `PointOfInterest.description` (`map_service`, тот же слой «ВОВ»,
 * что на карте). Фото для пазла и видео ищем в записях, у которых уже стоит
 * `poi_id` этой точки: `archive_service` (`/entries?poi_id=`) и
 * `media_service` (`/clips?poi_id=`) — обе ручки фильтр по точке поддерживают
 * давно, фронт им просто не пользовался. Если для точки ничего не нашли —
 * это не ошибка, а значит, у неё пока нет фото или видео в архиве.
 */

export interface PlaceDetails {
  id: string
  kind: PoiKind
  title: string
  description: string
  dateText: string
  /** Фото места для детского пазла — из народного архива, запасной вариант — фото «Живого фото». */
  photoUrl: string | null
  /** Готовый ролик, привязанный к этой точке. Есть не у каждой точки. */
  videoUrl: string | null
  source: DataSource
}

export class PlaceNotFoundError extends Error {
  constructor() {
    super('Место не найдено — возможно, ссылка на метке устарела')
    this.name = 'PlaceNotFoundError'
  }
}

interface EntryRow {
  media_url: string | null
}

interface ClipRow {
  source_photo_url: string
  video_url: string | null
  status: 'queued' | 'processing' | 'ready' | 'failed'
}

/** Первое фото места из народного архива — самая надёжная реставрация: люди сами проверяют записи. */
async function fetchArchivePhoto(poiId: string): Promise<string | null> {
  try {
    const entries = await apiRequest<EntryRow[]>('GET', 'archive', '/entries', { query: { poi_id: poiId, limit: 20 } })
    return entries.find((entry) => entry.media_url)?.media_url ?? null
  } catch {
    // Архив не ответил — фото для пазла просто не покажем, это не критично для экрана.
    return null
  }
}

/** Фото и видео из «Живого фото»: фото — запасной вариант для пазла, видео — только готовое (`ready`). */
async function fetchClipMedia(poiId: string): Promise<{ photoUrl: string | null; videoUrl: string | null }> {
  try {
    const clips = await apiRequest<ClipRow[]>('GET', 'media', '/clips', { query: { poi_id: poiId, limit: 10 } })
    return {
      photoUrl: clips.find((clip) => clip.source_photo_url)?.source_photo_url ?? null,
      videoUrl: clips.find((clip) => clip.status === 'ready' && clip.video_url)?.video_url ?? null,
    }
  } catch {
    return { photoUrl: null, videoUrl: null }
  }
}

export async function fetchPlace(poiId: string): Promise<PlaceDetails> {
  const { data: pois, source } = await listPoi()
  const poi = pois.find((item) => item.id === poiId)
  if (!poi) throw new PlaceNotFoundError()

  const [archivePhoto, clipMedia] = await Promise.all([fetchArchivePhoto(poiId), fetchClipMedia(poiId)])

  return {
    id: poi.id,
    kind: poi.kind,
    title: poi.title,
    description: poi.description,
    dateText: poi.date_text,
    photoUrl: archivePhoto ?? clipMedia.photoUrl,
    videoUrl: clipMedia.videoUrl,
    source,
  }
}
