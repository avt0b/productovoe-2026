import { apiRequest } from '@/core/api'

import * as mock from './mock'

/** Заглушка вместо сервиса: праздник можно посмотреть и в демо-режиме, без аккаунта. */
export const MOCK = import.meta.env.VITE_MOCK_NEW_API === 'true'

/** Роли, которые выдаёт метка, — `GRANTABLE_ROLES` в user_service. */
export type GrantedRole = 'searcher' | 'local_historian'

export interface RoleGrantRequest {
  /** Ключ с метки. */
  key: string
  /** Кому — id аккаунта, открытого на телефоне. */
  user_id: string
  /** Ник — только для журнала сервиса: ники не уникальны. */
  nickname: string
}

export interface RoleGrantResult {
  user_id: string
  role: GrantedRole
  previous_role: string
  /** Роль уже была: ничего не поменялось, но праздник всё равно. */
  already: boolean
}

/**
 * Обменять ключ с метки на роль. Без токена: разрешение даёт сам ключ, а
 * кому выдать — `user_id` в теле.
 */
export function redeemRoleGrant(body: RoleGrantRequest): Promise<RoleGrantResult> {
  if (MOCK) return mock.redeemRoleGrant(body)
  return apiRequest('POST', 'users', '/role-grants/redeem', { body })
}
