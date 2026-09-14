import { withLatency } from '@/core/mock'

/**
 * Данные окна «Профиль».
 *
 * Имя, подпись, город и аватар берутся из сессии — они есть у любого
 * пользователя. Здесь только то, что придёт из `user_service`: достижения,
 * древо, контакты. Пока заглушка из макета.
 *
 * Телефон и почта в макете выглядели как настоящие — такие данные могут
 * оказаться чьими-то реальными. В заглушке они заведомо демонстрационные.
 */

export interface ProfileCounter {
  value: number
  label: string
  accent?: boolean
}

export interface Ancestor {
  id: string
  name: string
  lifespan: string
  photo: string
  badge: string
  badgeIcon: string
  badgeTone: 'primary' | 'secondary'
}

export interface Badge {
  id: string
  title: string
  subtitle: string
  icon: string
  tone: 'primary' | 'secondary' | 'tertiary'
  filled?: boolean
}

export interface Contact {
  id: string
  label: string
  value: string
  icon: string
}

export interface AppSetting {
  id: string
  title: string
  description: string
  icon: string
  tone: 'secondary' | 'neutral'
  enabled: boolean
}

export interface ProfileOverview {
  experience: string
  counters: ProfileCounter[]
  expedition: {
    title: string
    season: string
    nextRank: string
    progress: number
    hint: string
  }
  ancestors: Ancestor[]
  badges: Badge[]
  badgesTotal: number
  contacts: Contact[]
  settings: AppSetting[]
  curator: string
  version: string
}

const OVERVIEW: ProfileOverview = {
  experience: 'Стаж 3 года',
  counters: [
    { value: 7, label: 'маршрутов пройдено' },
    { value: 3, label: 'находки проверено' },
    { value: 1250, label: 'очков следопыта', accent: true },
  ],
  expedition: {
    title: 'Участник экспедиции «Вахта Памяти 2024»',
    season: 'Сезон VI',
    nextRank: 'До ранга «Полевой следопыт II степени»',
    progress: 80,
    hint: 'Осталось подтвердить 1 найденный артефакт или пройти 3 км по рубежу Кривцовского мемориала.',
  },
  ancestors: [
    {
      id: 'voronov',
      name: 'Сержант Воронов А.Г.',
      lifespan: '1919 – 1944 • Стрелковый полк',
      photo:
        'https://lh3.googleusercontent.com/aida-public/AB6AXuBZ72rBXJF2vJzCn_HnrC-k8hj7ZTM6q5yjHpQHNzU89l7tGgQ7OkevhwiyG6AehzoaT_5jGfGXYSWeEDNRnriZKAo6yVeZR_jcBOoIJZw2JqqByjEHboU-7Y9tMewoPBsqz6tdKRBrowycBIXbatpOV_nJCB47l2FELgcK5-0mgP9ny5PEfd-6r-kkUpiEtePpLC7P8F-oA7yNTJcVsUuQFHTyqL6hqbXN2DNrdw5IkP3kAZYBZ5FG',
      badge: 'Маршрут подвига нанесен',
      badgeIcon: 'verified_user',
      badgeTone: 'primary',
    },
    {
      id: 'smirnov',
      name: 'Рядовой Смирнов П.И.',
      lifespan: '1923 – 1989 • Танковая бригада',
      photo:
        'https://lh3.googleusercontent.com/aida-public/AB6AXuB3n9Lnc73lnPU5J8nGUwt8NHOtAScAXMu3rFfXnJ_uczp47SHcaNRZdHMIc9Z5ITsqwMLKM9qXfviiP51VrMKj6cDBqULC6CJHQA2IfBocYI_DmSpL80yGyTnzhTODPcCyqaR3mzsGncfRdOsxn3seujBVJMW9vY438grUh_7vlmh5nzSEQRWoCnKd1zVPrwaenD_H7vF_sGPStqJ7oUOdKgN6WOOTeVahJHZCrDsLhRzn2cc-IQ0Y',
      badge: 'Архивная справка ЦАМО',
      badgeIcon: 'assignment_turned_in',
      badgeTone: 'secondary',
    },
  ],
  badges: [
    { id: 'km', title: '10 км рубежей', subtitle: 'Май 2024', icon: 'hiking', tone: 'primary' },
    { id: 'radio', title: 'Юный радист', subtitle: 'Квест штаба', icon: 'cell_tower', tone: 'secondary' },
    { id: 'keeper', title: 'Хранитель истории', subtitle: '3 реликвии', icon: 'auto_stories', tone: 'tertiary', filled: true },
  ],
  badgesTotal: 12,
  contacts: [
    { id: 'phone', label: 'Номер телефона', value: '+7 (900) 000-00-00', icon: 'call' },
    { id: 'email', label: 'Электронная почта', value: 'demo@marshruty.ru', icon: 'mail' },
    { id: 'city', label: 'Город базирования', value: 'Орёл • Орловско-Курская дуга', icon: 'home_pin' },
  ],
  settings: [
    {
      id: 'offline-maps',
      title: 'Оффлайн-карты рубежей',
      description: 'Загружен сектор «Орловский плацдарм» (1.2 ГБ)',
      icon: 'download_for_offline',
      tone: 'secondary',
      enabled: true,
    },
    {
      id: 'dig-alerts',
      title: 'Уведомления о раскопках рядом',
      description: 'Оповещения в радиусе 15 км от отряда',
      icon: 'radar',
      tone: 'neutral',
      enabled: true,
    },
    {
      id: 'audio-guides',
      title: 'Звуки и аудиогиды',
      description: 'Автозапуск истории при приближении к памятникам',
      icon: 'headphones',
      tone: 'neutral',
      enabled: true,
    },
  ],
  curator: 'Куратор майор В.С. Потапов на связи',
  version: '«Маршруты победы» v0.1.0 (каркас)',
}

export function fetchProfile(): Promise<ProfileOverview> {
  return withLatency(OVERVIEW)
}
