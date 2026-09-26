import type { GrantedRole } from './api'

export interface Rank {
  title: string
  icon: string
  /** Что роль открывает — то же, что в профиле (`ROLES` в modules/profile). */
  perks: readonly { icon: string; text: string }[]
}

/**
 * Звания для праздника. Списки повторяют профиль и правила `core/session/roles.ts`:
 * модули друг друга не импортируют, поэтому это копия — меняются там, меняйте и здесь.
 */
export const RANKS: Record<GrantedRole, Rank> = {
  searcher: {
    title: 'Поисковик',
    icon: 'person_search',
    perks: [
      { icon: 'military_tech', text: 'Отмечать места «Последнего боя»' },
      { icon: 'groups', text: 'Заводить отряд, выезды и сборы' },
      { icon: 'verified', text: 'Проверять народный архив' },
    ],
  },
  local_historian: {
    title: 'Краевед',
    icon: 'history_edu',
    perks: [
      { icon: 'directions_walk', text: 'Водить экскурсии' },
      { icon: 'route', text: 'Вести свои маршруты' },
      { icon: 'verified', text: 'Проверять народный архив' },
    ],
  },
}
