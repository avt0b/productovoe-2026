import { ApiError } from '@/core/api'
import { withLatency } from '@/core/mock'

import type { GrantedRole, RoleGrantRequest, RoleGrantResult } from './api'

/** Ключи заглушки — посмотреть праздник в браузере без меток и сервера. */
const DEMO_KEYS: Record<string, GrantedRole> = {
  'demo-searcher': 'searcher',
  'demo-historian': 'local_historian',
}

export function redeemRoleGrant(body: RoleGrantRequest): Promise<RoleGrantResult> {
  const role = DEMO_KEYS[body.key]
  if (!role) {
    return withLatency(null, 900).then(() => Promise.reject(new ApiError(404, 'Метка не подходит')))
  }
  // Подольше обычного: иначе экран «Проверяем метку…» не успеть разглядеть.
  return withLatency({ user_id: body.user_id, role, previous_role: 'family', already: false }, 900)
}
