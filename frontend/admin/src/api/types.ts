/** Типы ответов admin_service. Держим в соответствии с pydantic-схемами бэка. */

export type AdminRole = 'superadmin' | 'admin' | 'moderator' | 'viewer'

export interface AdminOut {
  id: string
  email: string
  full_name: string
  role: AdminRole
  is_active: boolean
  totp_enabled: boolean
  last_login_at: string | null
  created_at: string
}

export interface MeResponse extends AdminOut {
  mfa_satisfied: boolean
  totp_required_by_policy: boolean
  unused_recovery_codes: number
}

export interface LoginResponse {
  mfa_required: boolean
  mfa_token: string | null
  mfa_expires_in: number | null
  access_token: string | null
  refresh_token: string | null
  token_type: string
  expires_in: number | null
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface TotpSetup {
  secret: string
  otpauth_uri: string
}

export interface RecoveryCodes {
  codes: string[]
  generated_at: string
}

/** Плитка KPI дашборда. `value === null` — сервис недоступен, рисуем прочерк. */
export interface DashboardTile {
  key: string
  label: string
  value: number | null
  hint: string | null
  tone: 'neutral' | 'attention' | 'error'
}

export interface ServiceBlock {
  available: boolean
  title: string
  stats?: Record<string, unknown>
  error?: string
}

export interface DashboardOverview {
  generated_at: string
  tiles: DashboardTile[]
  summary: Record<string, unknown>
  services: Record<string, ServiceBlock>
  degraded: string[]
  not_implemented: string[]
  recent_audit: AuditEntry[]
}

export interface SeriesPoint {
  date: string
  value: number
}

export interface Series {
  key: string
  label: string
  points: SeriesPoint[]
}

export interface Timeseries {
  days: number
  series: Series[]
}

export interface ServiceHealthRow {
  service: string
  title: string
  url: string
  ok: boolean
  status: string
  env: string
}

export interface HealthReport {
  checked_at: string
  services: ServiceHealthRow[]
  healthy: number
  total: number
}

export type AuditOutcome = 'success' | 'denied' | 'failed'

export interface AuditEntry {
  id: string
  actor_id: string
  actor_email: string
  actor_role: string
  action: string
  target_service: string
  target_type: string
  target_id: string
  target_label: string
  outcome: AuditOutcome
  message: string
  payload: Record<string, unknown>
  ip: string
  created_at: string
}

/** Постраничный ответ — форма одинакова у всех списков. */
export interface Page<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export type PlatformRole = 'family' | 'searcher' | 'local_historian' | 'mentor' | 'moderator'

export interface PlatformUser {
  id: string
  email: string
  role: PlatformRole
  is_root: boolean
  is_active: boolean
  created_at: string
}

export interface Profile {
  id: string
  display_name: string
  city: string
  bio: string
  avatar_url: string | null
  role: string
  squad_id: string | null
  is_verified: boolean
  subscribed_to_search: boolean
  alert_radius_km: number
  created_at: string
}

export type EntryStatus = 'pending' | 'verified' | 'rejected'
export type EntryKind = 'event' | 'soldier_card' | 'memory' | 'photo_story'

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
  verified_by?: string | null
  reviewed_at?: string | null
  review_note?: string
  created_at: string
}

export type LastStandStatus = 'discovered' | 'archive_confirmed' | 'remains_raised'

export interface LastStandPoint {
  id: string
  soldier_name: string
  unit: string
  lat: number
  lon: number
  circumstances?: string
  death_date?: string | null
  date_text?: string
  source?: string
  status: LastStandStatus
  created_by: string
  created_at: string
}

export interface Squad {
  id: string
  name: string
  region: string
  description: string
  contact: string
  leader_id: string
  created_at: string
}

export type NeedKind = 'volunteers' | 'funds' | 'equipment'
export type NeedStatus = 'open' | 'closed'

export interface SquadNeed {
  id: string
  squad_id: string
  kind: NeedKind
  title: string
  description: string
  target_amount: number | null
  collected_amount: number
  status: NeedStatus
  created_at: string
}

export interface Trip {
  id: string
  squad_id: string
  title: string
  location: string
  starts_on: string
  capacity: number
  description: string
  checklist: string
  created_at: string
}

export interface RouteItem {
  id: string
  title: string
  description: string
  mode: 'family' | 'general'
  city: string
  distance_km: number
  cover_url: string | null
  created_by: string
  is_published: boolean
  created_at: string
}

export type ClipStatus = 'queued' | 'processing' | 'ready' | 'failed'

export interface Clip {
  id: string
  soldier_name: string
  source_photo_url: string
  narration_text: string
  voice_style: string
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
