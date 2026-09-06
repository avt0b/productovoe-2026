/** Тонкие обёртки над эндпоинтами admin_service — по одной группе на раздел. */

import { api, request } from './client'
import type {
  AdminOut,
  AdminRole,
  ArchiveEntry,
  AuditEntry,
  Clip,
  ClipStatus,
  DashboardOverview,
  EntryKind,
  EntryStatus,
  HealthReport,
  LastStandPoint,
  LastStandStatus,
  LoginResponse,
  MeResponse,
  NeedKind,
  NeedStatus,
  Page,
  PlatformRole,
  PlatformUser,
  Profile,
  RecoveryCodes,
  RouteItem,
  Squad,
  SquadNeed,
  Timeseries,
  TokenPair,
  TotpSetup,
  Trip,
} from './types'

/**
 * Именно `type`, а не `interface`: интерфейсы в TypeScript не получают неявную
 * индексную сигнатуру и потому не подходят под `Record<string, …>` в клиенте.
 */
export type ListParams = {
  query?: string
  limit?: number
  offset?: number
}

// --- аутентификация --------------------------------------------------------

export const authApi = {
  login: (email: string, password: string) =>
    request<LoginResponse>('/admin/auth/login', {
      method: 'POST',
      body: { email, password },
      anonymous: true,
    }),

  loginMfa: (mfaToken: string, code: string) =>
    request<TokenPair>('/admin/auth/login/mfa', {
      method: 'POST',
      body: { mfa_token: mfaToken, code },
      anonymous: true,
    }),

  logout: (refreshToken: string) =>
    request<void>('/admin/auth/logout', {
      method: 'POST',
      body: { refresh_token: refreshToken },
      anonymous: true,
    }),

  /** Завершает все сессии администратора, включая текущую. */
  logoutEverywhere: () => api.post<void>('/admin/auth/logout-everywhere'),

  me: () => api.get<MeResponse>('/admin/auth/me'),

  changePassword: (currentPassword: string, newPassword: string) =>
    api.post<void>('/admin/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),

  totpSetup: () => api.post<TotpSetup>('/admin/auth/totp/setup'),
  totpConfirm: (code: string) => api.post<RecoveryCodes>('/admin/auth/totp/confirm', { code }),
  totpDisable: (password: string, code: string) =>
    api.post<void>('/admin/auth/totp/disable', { password, code }),
  regenerateRecoveryCodes: (code: string) =>
    api.post<RecoveryCodes>('/admin/auth/totp/recovery-codes', { code }),
}

// --- дашборд ---------------------------------------------------------------

export const dashboardApi = {
  overview: (recentActions = 8) =>
    api.get<DashboardOverview>('/admin/dashboard/overview', { recent_actions: recentActions }),
  timeseries: (days = 30) => api.get<Timeseries>('/admin/dashboard/timeseries', { days }),
  health: () => api.get<HealthReport>('/admin/dashboard/health'),
}

// --- операции над данными платформы ---------------------------------------

export const opsApi = {
  // Пользователи и роли
  users: (params: ListParams & { role?: string; is_active?: boolean } = {}) =>
    api.get<Page<PlatformUser>>('/admin/ops/users', params),
  setUserRole: (userId: string, role: PlatformRole) =>
    api.patch<PlatformUser>(`/admin/ops/users/${userId}/role`, { role }),
  setUserActive: (userId: string, isActive: boolean, reason = '') =>
    api.patch<PlatformUser>(`/admin/ops/users/${userId}/active`, { reason }, { is_active: isActive }),
  setUserRoot: (userId: string, isRoot: boolean) =>
    api.patch<PlatformUser>(`/admin/ops/users/${userId}/root`, undefined, { is_root: isRoot }),

  // Профили и верификация статуса
  profiles: (params: ListParams & { role?: string; is_verified?: boolean } = {}) =>
    api.get<Page<Profile>>('/admin/ops/profiles', params),
  verifyProfile: (profileId: string, isVerified: boolean, note = '') =>
    api.patch<Profile>(`/admin/ops/profiles/${profileId}/verify`, { note }, { is_verified: isVerified }),

  // Народный архив
  entries: (params: ListParams & { status?: EntryStatus; kind?: EntryKind } = {}) =>
    api.get<Page<ArchiveEntry>>('/admin/ops/entries', params),
  verifyEntry: (entryId: string, note = '') =>
    api.post<ArchiveEntry>(`/admin/ops/entries/${entryId}/verify`, { note }),
  rejectEntry: (entryId: string, note = '') =>
    api.post<ArchiveEntry>(`/admin/ops/entries/${entryId}/reject`, { note }),

  // «Последний бой»
  lastStand: (params: ListParams & { status?: LastStandStatus } = {}) =>
    api.get<Page<LastStandPoint>>('/admin/ops/last-stand', params),
  setLastStandStatus: (pointId: string, status: LastStandStatus, reason = '') =>
    api.patch<LastStandPoint>(`/admin/ops/last-stand/${pointId}/status`, { status, reason }),
  deleteLastStand: (pointId: string, reason = '') =>
    api.delete<void>(`/admin/ops/last-stand/${pointId}`, { reason }),

  // Поисковый штаб
  squads: (params: ListParams = {}) => api.get<Page<Squad>>('/admin/ops/squads', params),
  needs: (params: ListParams & { status?: NeedStatus; kind?: NeedKind; squad_id?: string } = {}) =>
    api.get<Page<SquadNeed>>('/admin/ops/needs', params),
  closeNeed: (needId: string, reason = '') =>
    api.post<SquadNeed>(`/admin/ops/needs/${needId}/close`, { reason }),
  trips: (params: ListParams & { upcoming_only?: boolean; squad_id?: string } = {}) =>
    api.get<Page<Trip>>('/admin/ops/trips', params),

  // Маршруты
  routes: (params: ListParams & { is_published?: boolean; mode?: string } = {}) =>
    api.get<Page<RouteItem>>('/admin/ops/routes', params),
  publishRoute: (routeId: string, isPublished: boolean) =>
    api.post<RouteItem>(`/admin/ops/routes/${routeId}/publish`, { is_published: isPublished }),

  // «Живое фото»
  clips: (params: ListParams & { status?: ClipStatus; is_public?: boolean } = {}) =>
    api.get<Page<Clip>>('/admin/ops/clips', params),
  retryClip: (clipId: string) => api.post<Clip>(`/admin/ops/clips/${clipId}/retry`),
  setClipVisibility: (clipId: string, isPublic: boolean, reason = '') =>
    api.patch<Clip>(`/admin/ops/clips/${clipId}/visibility`, { is_public: isPublic, reason }),
}

// --- учётки администраторов (superadmin) -----------------------------------

export const accountsApi = {
  list: (params: ListParams & { role?: AdminRole; is_active?: boolean } = {}) =>
    api.get<Page<AdminOut>>('/admin/accounts', params),
  create: (payload: { email: string; password: string; full_name: string; role: AdminRole }) =>
    api.post<AdminOut>('/admin/accounts', payload),
  update: (adminId: string, payload: { full_name?: string; role?: AdminRole }) =>
    api.patch<AdminOut>(`/admin/accounts/${adminId}`, payload),
  setActive: (adminId: string, isActive: boolean) =>
    api.patch<AdminOut>(`/admin/accounts/${adminId}/active`, { is_active: isActive }),
  resetPassword: (adminId: string, newPassword: string) =>
    api.post<AdminOut>(`/admin/accounts/${adminId}/reset-password`, { new_password: newPassword }),
  resetTotp: (adminId: string) => api.post<AdminOut>(`/admin/accounts/${adminId}/reset-totp`),
  remove: (adminId: string) => api.delete<void>(`/admin/accounts/${adminId}`),
}

// --- журнал аудита ---------------------------------------------------------

export const auditApi = {
  list: (
    params: ListParams & {
      actor_id?: string
      action?: string
      target_service?: string
      outcome?: string
      days?: number
    } = {},
  ) => api.get<Page<AuditEntry>>('/admin/audit', params),
  stats: (days = 7) =>
    api.get<{ total: number; by_action: Record<string, number>; by_outcome: Record<string, number> }>(
      '/admin/audit/stats',
      { days },
    ),
}
