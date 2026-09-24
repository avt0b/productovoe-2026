import type { SessionUser, UserRole } from './types'

/**
 * Кто что может — повтор проверок сервисов, чтобы не показывать действие,
 * которое всё равно закончится ответом 403. Решает всё равно сервис: здесь
 * только то, какие кнопки рисовать.
 */

type Rule = ReadonlySet<UserRole>

const rule = (...roles: UserRole[]): Rule => new Set(roles)

/** Проверяет записи народного архива — `VERIFIER_ROLES` в archive_service. */
const ARCHIVE_VERIFIERS = rule('searcher', 'local_historian', 'mentor', 'moderator')
/** Подтверждает профиль исследователя — `_VERIFIER_ROLES` в user_service; поисковика там нет. */
const PROFILE_VERIFIERS = rule('local_historian', 'mentor', 'moderator')
/** Добавляет места «Последнего боя» — `_CONTRIBUTOR_ROLES` в map_service. */
const LAST_STAND_CONTRIBUTORS = rule('searcher', 'local_historian', 'mentor', 'moderator')
/** Создаёт отряды — `SQUAD_CREATOR_ROLES` в search_hq_service. */
const SQUAD_CREATORS = rule('searcher', 'moderator')
/** Водит экскурсии — `GUIDE_ROLES` в search_hq_service. */
const GUIDES = rule('local_historian', 'mentor', 'moderator')
/** Ведёт маршруты: черновики, точки, публикация — `AUTHOR_ROLES` в route_service. */
const ROUTE_AUTHORS = rule('local_historian', 'mentor', 'moderator')
/** Дополняет слой «ВОВ» на карте — `_CONTRIBUTOR_ROLES` в map_service. */
const POI_CONTRIBUTORS = rule('searcher', 'local_historian', 'mentor', 'moderator')

function allowed(user: SessionUser | null | undefined, roles: Rule): boolean {
  if (!user) return false
  return user.isRoot === true || (user.role !== undefined && roles.has(user.role))
}

export const can = {
  verifyArchive: (user: SessionUser | null | undefined) => allowed(user, ARCHIVE_VERIFIERS),
  verifyProfile: (user: SessionUser | null | undefined) => allowed(user, PROFILE_VERIFIERS),
  addLastStand: (user: SessionUser | null | undefined) => allowed(user, LAST_STAND_CONTRIBUTORS),
  moderate: (user: SessionUser | null | undefined) => allowed(user, rule('moderator')),
  createSquad: (user: SessionUser | null | undefined) => allowed(user, SQUAD_CREATORS),
  guide: (user: SessionUser | null | undefined) => allowed(user, GUIDES),
  authorRoute: (user: SessionUser | null | undefined) => allowed(user, ROUTE_AUTHORS),
  addPoi: (user: SessionUser | null | undefined) => allowed(user, POI_CONTRIBUTORS),
}
