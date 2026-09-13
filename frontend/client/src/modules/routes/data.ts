import { withLatency } from '@/core/mock'

/**
 * Данные окна «Маршруты».
 *
 * Пока заглушка из макета. Когда подключим `route_service` и `map_service`,
 * поменяется только тело `fetchRoutesOverview` — типы и экран останутся.
 */

export interface RouteFilter {
  id: string
  title: string
  icon: string
  /** Подсвеченная категория, даже когда фильтр не выбран («Для детей»). */
  highlight?: boolean
  /** Цвет иконки у невыбранного фильтра. */
  iconClass?: string
  filledIcon?: boolean
}

export type MapPinKind = 'you' | 'memorial' | 'battle'

export interface MapPin {
  id: string
  kind: MapPinKind
  title: string
  subtitle?: string
  /** Координаты на нарисованной карте, в единицах холста макета 390×460. */
  x: number
  y: number
}

export interface FeaturedRoute {
  id: string
  title: string
  description: string
  distanceKm: number
  durationMinutes: number
  difficulty: string
  rating: number
  reviews: number
  /** Подпись маршрута в углу карты. */
  mapLabel: string
  /** Метка, с которой начинается маршрут, — её подсвечиваем. */
  pinId: string
  /** Первая точка маршрута — сюда ведёт «Начать путешествие». */
  startPointId: string
  task: {
    title: string
    text: string
    reward: string
  }
}

export interface RoutesOverview {
  filters: RouteFilter[]
  pins: MapPin[]
  featured: FeaturedRoute
}

const OVERVIEW: RoutesOverview = {
  filters: [
    { id: 'walking', title: 'Пешие (до 3 км)', icon: 'directions_walk' },
    { id: 'kids', title: 'Для детей', icon: 'star', highlight: true, iconClass: 'text-tertiary', filledIcon: true },
    { id: 'tanks', title: 'Танковые рубежи', icon: 'military_tech', iconClass: 'text-secondary' },
    { id: 'normandie', title: 'Нормандия-Неман', icon: 'flight', iconClass: 'text-secondary' },
    { id: 'audio', title: 'С аудиогидом', icon: 'headphones', iconClass: 'text-primary' },
  ],
  pins: [
    { id: 'you', kind: 'you', title: 'Вы здесь', x: 64, y: 270 },
    { id: 'signal-node', kind: 'memorial', title: 'Узел связи', subtitle: 'и окопы 1941', x: 175, y: 185 },
    { id: 'defense-line', kind: 'battle', title: 'Рубеж обороны', x: 78, y: 108 },
    { id: 'kromy', kind: 'battle', title: 'Кромской рубеж', x: 292, y: 95 },
  ],
  featured: {
    id: 'kromy-sailors',
    title: 'Кромской рубеж: по следам моряков',
    description: 'Мемориальная тропа героев 116-й отдельной морской стрелковой бригады',
    distanceKm: 2.8,
    durationMinutes: 45,
    difficulty: 'Легкий',
    rating: 4.9,
    reviews: 128,
    mapLabel: 'Маршрут «Тропа памяти»',
    pinId: 'kromy',
    startPointId: 'kromy-line',
    task: {
      title: 'Задание исследователя',
      text: 'Расшифруйте радиограмму Морзе на 2-й точке маршрута и получите памятный значок',
      reward: '«Юный связист»',
    },
  },
}

export function fetchRoutesOverview(): Promise<RoutesOverview> {
  return withLatency(OVERVIEW)
}
