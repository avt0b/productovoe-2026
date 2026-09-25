import { apiRequest } from '@/core/api'
import type { LatLon } from '@/core/geo'

/**
 * Данные окна «Память».
 *
 * - **Народный архив** — `archive_service` (`/entries`): каждый может
 *   предложить событие, карточку бойца, воспоминание; краевед или поисковик
 *   подтверждает, и запись появляется в общей ленте.
 * - **Живое фото** — `media_service` (`/clips`): заявка на оживление фото
 *   бойца, её статус и общий мемориал. Саму генерацию делает отдельный
 *   воркер; пока его нет, заявки стоят в очереди — экран говорит об этом.
 *
 * Типы повторяют схемы сервисов, поля в snake_case.
 */

export type EntryKind = 'event' | 'soldier_card' | 'memory' | 'photo_story'
export type EntryStatus = 'pending' | 'verified' | 'rejected'

export interface ArchiveEntry {
  id: string
  kind: EntryKind
  title: string
  body: string
  lat: number | null
  lon: number | null
  event_date: string | null
  date_text: string
  media_url: string | null
  submitted_by: string
  status: EntryStatus
  verified_by: string | null
  reviewed_at: string | null
  /** Заметка проверяющего — только автору и проверяющим. */
  review_note?: string
  created_at: string
}

export interface EntryDraft {
  kind: EntryKind
  title: string
  body: string
  lat: number | null
  lon: number | null
  date_text: string
  media_url: string | null
}

export const ENTRY_KINDS: Record<EntryKind, { title: string; icon: string }> = {
  event: { title: 'Событие', icon: 'history_edu' },
  soldier_card: { title: 'Карточка бойца', icon: 'military_tech' },
  memory: { title: 'Воспоминание', icon: 'record_voice_over' },
  photo_story: { title: 'Фото и история', icon: 'photo_camera' },
}

/** «Подтверждено» — латунью, как всё наградное; ожидание — нейтральное, чтобы не спорить со значком. */
export const ENTRY_STATUS: Record<EntryStatus, { title: string; icon: string; class: string }> = {
  pending: { title: 'На проверке', icon: 'hourglass_top', class: 'bg-surface-container-high text-on-surface-variant' },
  verified: { title: 'Подтверждено', icon: 'verified', class: 'bg-tertiary-fixed text-on-tertiary-fixed' },
  rejected: { title: 'Не подтверждено', icon: 'cancel', class: 'bg-error-container text-on-error-container' },
}

export type ClipStatus = 'queued' | 'processing' | 'ready' | 'failed'
export type VoiceStyle = 'era_male' | 'era_female' | 'neutral'

export interface Clip {
  id: string
  soldier_name: string
  source_photo_url: string
  narration_text: string
  voice_style: VoiceStyle
  submitted_by: string
  consent_memorial_use: boolean
  is_public: boolean
  status: ClipStatus
  video_url: string | null
  error: string
  rendered_at: string | null
  archive_entry_id: string | null
  created_at: string
}

export interface ClipDraft {
  soldier_name: string
  source_photo_url: string
  narration_text: string
  voice_style: VoiceStyle
  is_public: boolean
  consent_memorial_use: boolean
}

export const VOICES: Record<VoiceStyle, string> = {
  era_male: 'Мужской голос эпохи',
  era_female: 'Женский голос эпохи',
  neutral: 'Нейтральный голос',
}

export const CLIP_STATUS: Record<ClipStatus, { title: string; icon: string; class: string }> = {
  queued: { title: 'В очереди', icon: 'schedule', class: 'bg-surface-container-high text-on-surface-variant' },
  processing: { title: 'Оживляем', icon: 'progress_activity', class: 'bg-tertiary-fixed text-on-tertiary-fixed' },
  ready: { title: 'Готово', icon: 'check_circle', class: 'bg-secondary-container text-on-secondary-container' },
  failed: { title: 'Не получилось', icon: 'error', class: 'bg-error-container text-on-error-container' },
}

/** Текст по умолчанию — из кейса, тот же, что у `media_service`. */
export const DEFAULT_NARRATION = 'Я сделал это, чтобы ты жил и видел голубое небо. Помни меня.'

// --- народный архив ---

/** Подтверждённые записи — видны всем, аккаунт не нужен. `q` ищет по заголовку и тексту. */
export function fetchPublicEntries(kind: EntryKind | null, q = ''): Promise<ArchiveEntry[]> {
  return apiRequest('GET', 'archive', '/entries', { query: { kind, q: q.trim() || null, limit: 200 } })
}

/** Неподтверждённая запись рядом — сервис отдаёт только вид, заголовок и место. */
export interface NearbyPending {
  id: string
  kind: EntryKind
  title: string
  lat: number | null
  lon: number | null
}

/** Градусов широты в километре — для прямоугольника поиска вокруг точки. */
const DEG_PER_KM = 1 / 111

/**
 * Записи «на проверке» вокруг точки: «рядом есть неподтверждённая заметка —
 * помогите проверить». Сервис ищет прямоугольником; долготу растягиваем по
 * широте, чтобы на Орловщине он был близок к квадрату, а не к полоске.
 */
export function fetchNearbyPending(center: LatLon, radiusKm: number): Promise<NearbyPending[]> {
  const dLat = radiusKm * DEG_PER_KM
  const dLon = dLat / Math.max(0.2, Math.cos((center.lat * Math.PI) / 180))
  return apiRequest('GET', 'archive', '/entries/nearby-pending', {
    query: {
      min_lat: center.lat - dLat,
      min_lon: center.lon - dLon,
      max_lat: center.lat + dLat,
      max_lon: center.lon + dLon,
      limit: 50,
    },
  })
}

export function fetchMyEntries(): Promise<ArchiveEntry[]> {
  return apiRequest('GET', 'archive', '/entries/mine', { auth: true })
}

/** Очередь проверки — краеведу и поисковику (`VERIFIER_ROLES` в archive_service). */
export function fetchModerationQueue(): Promise<ArchiveEntry[]> {
  return apiRequest('GET', 'archive', '/entries/moderation', { auth: true })
}

export function proposeEntry(draft: EntryDraft): Promise<ArchiveEntry> {
  return apiRequest('POST', 'archive', '/entries', { body: draft, auth: true })
}

/**
 * Поправить свою запись — пока она на проверке (`update` в archive_service:
 * автору проверенную запись менять нельзя, это уже дело краеведа).
 */
export function updateEntry(entryId: string, patch: Partial<EntryDraft>): Promise<ArchiveEntry> {
  return apiRequest('PATCH', 'archive', `/entries/${encodeURIComponent(entryId)}`, { body: patch, auth: true })
}

/** Убрать свою запись — тоже пока она на проверке. */
export function deleteEntry(entryId: string): Promise<void> {
  return apiRequest('DELETE', 'archive', `/entries/${encodeURIComponent(entryId)}`, { auth: true })
}

export function reviewEntry(entryId: string, verdict: 'verify' | 'reject', note: string): Promise<ArchiveEntry> {
  return apiRequest('POST', 'archive', `/entries/${encodeURIComponent(entryId)}/${verdict}`, { body: { note }, auth: true })
}

// --- живое фото ---

/** Общий мемориал: только готовые клипы, которые семьи разрешили показывать. */
export function fetchMemorial(): Promise<Clip[]> {
  return apiRequest('GET', 'media', '/clips', { query: { limit: 50 } })
}

export function fetchMyClips(): Promise<Clip[]> {
  return apiRequest('GET', 'media', '/clips/mine', { auth: true })
}

export function requestClip(draft: ClipDraft): Promise<Clip> {
  return apiRequest('POST', 'media', '/clips', { body: draft, auth: true })
}

export function retryClip(clipId: string): Promise<Clip> {
  return apiRequest('POST', 'media', `/clips/${encodeURIComponent(clipId)}/retry`, { auth: true })
}

/** Показать в общем мемориале или оставить семье. */
export function setClipPublic(clipId: string, isPublic: boolean): Promise<Clip> {
  return apiRequest('PATCH', 'media', `/clips/${encodeURIComponent(clipId)}`, { body: { is_public: isPublic }, auth: true })
}

export type UploadService = 'media' | 'archive'

/** Фото с телефона — в хранилище сервиса; обратно приходит адрес, который и уходит в заявку. */
export async function uploadPhoto(service: UploadService, file: File): Promise<string> {
  const body = new FormData()
  body.append('file', file)
  const { url } = await apiRequest<{ url: string }>('POST', service, '/uploads', { body, auth: true })
  return url
}

/** Убрать свой клип из семейного архива — вместе с ним уходит и из мемориала. */
export function deleteClip(clipId: string): Promise<void> {
  return apiRequest('DELETE', 'media', `/clips/${encodeURIComponent(clipId)}`, { auth: true })
}

export function shareClip(clipId: string, recipient: string, note: string): Promise<unknown> {
  return apiRequest('POST', 'media', `/clips/${encodeURIComponent(clipId)}/shares`, { body: { recipient, note }, auth: true })
}
