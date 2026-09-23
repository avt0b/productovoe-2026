import type { UserRole } from '@/core/session'

import { fetchMyAchievements, fetchMyProfile, type Achievement, type Profile } from './api'

/** Профиль и достижения одним запросом экрана. */
export interface ProfileOverview {
  profile: Profile
  achievements: Achievement[]
}

/**
 * Загрузка экрана. Достижения идут отдельной ручкой параллельно с профилем:
 * в профиле они тоже есть, но так список можно обновить, не перезапрашивая
 * всё остальное.
 */
export async function loadProfile(): Promise<ProfileOverview> {
  const [profile, achievements] = await Promise.all([fetchMyProfile(), fetchMyAchievements()])
  return { profile, achievements }
}

const ROLE_TITLES: Record<string, string> = {
  family: 'Участник маршрутов',
  searcher: 'Поисковик',
  local_historian: 'Краевед',
  mentor: 'Наставник',
  moderator: 'Модератор',
}

export function roleTitle(role: string | UserRole): string {
  return ROLE_TITLES[role] ?? ROLE_TITLES.family
}

/**
 * Названия достижений. Бэкенд хранит только код и дату — справочник живёт
 * здесь. Коды выдают route_service, search_hq_service и archive_service;
 * незнакомый код покажется как есть, чтобы новое достижение не пропало
 * из интерфейса молча.
 */
const ACHIEVEMENTS: Record<string, { title: string; hint: string; icon: string }> = {
  first_route_completed: {
    title: 'Первый маршрут',
    hint: 'Пройден семейный маршрут целиком',
    icon: 'hiking',
  },
  trip_volunteer: {
    title: 'Волонтёр выезда',
    hint: 'Участие в выезде поискового отряда',
    icon: 'volunteer_activism',
  },
  donor: {
    title: 'Опора отряда',
    hint: 'Поддержан целевой сбор',
    icon: 'payments',
  },
  archive_helper: {
    title: 'Хранитель архива',
    hint: 'Запись народного архива проверена',
    icon: 'inventory_2',
  },
}

export interface AchievementView {
  code: string
  title: string
  hint: string
  icon: string
  earnedAt: string
}

export function describeAchievement(achievement: Achievement): AchievementView {
  const known = ACHIEVEMENTS[achievement.code]
  return {
    code: achievement.code,
    title: known?.title ?? achievement.code,
    hint: known?.hint ?? 'Новое отличие',
    icon: known?.icon ?? 'military_tech',
    earnedAt: achievement.earned_at,
  }
}

/**
 * «в экспедиции с сентября 2026» — из `created_at` профиля.
 *
 * Месяц берётся из полной даты по частям: формат `{ month: 'long' }` сам по
 * себе даёт именительный падеж («сентябрь»), а в этой фразе нужен родительный.
 */
export function memberSince(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  const parts = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }).formatToParts(date)
  const month = parts.find((part) => part.type === 'month')?.value ?? ''
  const year = parts.find((part) => part.type === 'year')?.value ?? ''
  return month && year ? `${month} ${year}` : ''
}

export function formatDate(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }).format(date)
}
