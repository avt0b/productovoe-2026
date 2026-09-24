import type { SessionUser, UserRole } from './types'

/**
 * Кто что может — повтор проверок сервисов, чтобы не показывать действие,
 * которое всё равно закончится ответом 403. Решает всё равно сервис: здесь
 * только то, какие кнопки рисовать.
 */

type Rule = ReadonlySet<UserRole>

const rule = (...roles: UserRole[]): Rule => new Set(roles)

/** Проверяет записи народного архива — `VERIFIER_ROLES` в archive_service. */
const ARCHIVE_VERIFIERS = rule('searcher', 'local_historian')
/** Добавляет места «Последнего боя» — `_CONTRIBUTOR_ROLES` в map_service. */
const LAST_STAND_CONTRIBUTORS = rule('searcher', 'local_historian')
/** Создаёт отряды — `SQUAD_CREATOR_ROLES` в search_hq_service. */
const SQUAD_CREATORS = rule('searcher')
/** Водит экскурсии — `GUIDE_ROLES` в search_hq_service. */
const GUIDES = rule('local_historian')
/** Ведёт маршруты: черновики, точки, публикация — `AUTHOR_ROLES` в route_service. */
const ROUTE_AUTHORS = rule('local_historian')
/** Дополняет слой «ВОВ» на карте — `_CONTRIBUTOR_ROLES` в map_service. */
const POI_CONTRIBUTORS = rule('searcher', 'local_historian')

function allowed(user: SessionUser | null | undefined, roles: Rule): boolean {
  if (!user) return false
  return user.isRoot === true || (user.role !== undefined && roles.has(user.role))
}

export const can = {
  verifyArchive: (user: SessionUser | null | undefined) => allowed(user, ARCHIVE_VERIFIERS),
  /** Подтверждает профиль исследователя — теперь только администратор при одобрении заявки. */
  verifyProfile: (user: SessionUser | null | undefined) => user?.isRoot === true,
  addLastStand: (user: SessionUser | null | undefined) => allowed(user, LAST_STAND_CONTRIBUTORS),
  /** Стафф-права: стадии мест, правка чужого, снятие клипа — только администратор (`is_root`). */
  moderate: (user: SessionUser | null | undefined) => user?.isRoot === true,
  createSquad: (user: SessionUser | null | undefined) => allowed(user, SQUAD_CREATORS),
  guide: (user: SessionUser | null | undefined) => allowed(user, GUIDES),
  authorRoute: (user: SessionUser | null | undefined) => allowed(user, ROUTE_AUTHORS),
  addPoi: (user: SessionUser | null | undefined) => allowed(user, POI_CONTRIBUTORS),
}
