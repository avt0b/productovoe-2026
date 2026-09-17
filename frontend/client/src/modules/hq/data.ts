import { withLatency } from '@/core/mock'

/**
 * Данные окна «Штаб».
 *
 * Пока заглушка из макета. Когда подключим `search_hq_service`, поменяется
 * только тело `fetchHq`.
 */

export interface SeasonStat {
  value: number
  label: string
  tone: 'primary' | 'secondary' | 'tertiary'
}

export interface Season {
  kicker: string
  title: string
  stats: SeasonStat[]
  quote: string
}

export interface Campaign {
  id: string
  urgent: boolean
  daysLeft: number
  squad: string
  city: string
  purpose: string
  raised: number
  goal: number
  supporters: number
  /** Инициалы первых помощников для стопки аватаров. */
  supporterInitials: string[]
  minDonation: number
}

export interface ChecklistItem {
  id: string
  title: string
  done: boolean
}

export interface FieldEvent {
  id: string
  when: string
  title: string
  leader: string
  checklist: ChecklistItem[]
  seatsLeft: number
  seatsTotal: number
  free: boolean
}

export interface HqOverview {
  season: Season
  campaignsTotal: number
  campaign: Campaign
  event: FieldEvent
}

const OVERVIEW: HqOverview = {
  season: {
    kicker: 'Экспедиционный свод',
    title: '«Вахта Памяти 2024»',
    stats: [
      { value: 14, label: 'бойцов поднято', tone: 'primary' },
      { value: 3, label: 'воина преданы земле', tone: 'secondary' },
      { value: 2, label: 'имени установлено', tone: 'tertiary' },
    ],
    quote: '«Война не окончена, пока не похоронен последний солдат»',
  },
  campaignsTotal: 6,
  campaign: {
    id: 'vysota-spring',
    urgent: true,
    daysLeft: 8,
    squad: 'Поисковый отряд «Высота»',
    city: 'г. Орел',
    purpose:
      'Сбор на бензин для мотопомп и дизельный генератор для весенней поисковой экспедиции в глухие леса Болховского района.',
    raised: 35000,
    goal: 50000,
    supporters: 142,
    supporterInitials: ['АВ', 'ИП'],
    minDonation: 100,
  },
  event: {
    id: 'krupyshino-recon',
    when: 'Суббота, 14 сентября • 09:00 – 16:00',
    title: 'Разведка у села Крупышино: археология и топография',
    leader: 'Руководитель выезда — Михаил Смирнов, стаж 18 лет',
    checklist: [
      { id: 'boots', title: 'Резиновые сапоги (высокие)', done: true },
      { id: 'gloves', title: 'Плотные рабочие перчатки', done: false },
      { id: 'thermos', title: 'Термос с чаем и сухой паек', done: false },
      { id: 'phone', title: 'Заряженный телефон с приложением', done: true },
    ],
    seatsLeft: 4,
    seatsTotal: 15,
    free: true,
  },
}

export function fetchHq(): Promise<HqOverview> {
  return withLatency(OVERVIEW)
}
