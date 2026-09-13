import { withLatency } from '@/core/mock'

/**
 * Данные окна «Последний бой».
 *
 * Пока заглушка из макета. Когда подключим `archive_service` и `map_service`,
 * поменяется только тело `fetchLastStand`.
 */

/** Стадия находки: обнаружено и проверяется → подтверждено архивом → останки подняты. */
export type FindStatus = 'found' | 'confirmed' | 'raised'

export const STATUS_LABELS: Record<FindStatus, string> = {
  found: 'Обнаружено (проверка)',
  confirmed: 'Подтверждено архивом',
  raised: 'Останки подняты',
}

export interface SectorPin {
  id: string
  status: FindStatus
  label: string
  icon: string
  /** Положение на плане сектора, проценты от ширины и высоты. */
  x: number
  y: number
  recordId: string
}

export interface FindRecord {
  id: string
  stage: string
  square: string
  title: string
  period: string
  photos: { src: string; caption: string }[]
  coordinates: string
  source: string
  evidence: string
}

export interface LastStandOverview {
  alert: { title: string; distance: string; text: string }
  sector: string
  pins: SectorPin[]
  records: Record<string, FindRecord>
}

const OVERVIEW: LastStandOverview = {
  alert: {
    title: 'Внимание поисковика',
    distance: '5 км рядом',
    text: 'Обнаружено предположительное место боя осени 1941 г. Помогите архивистам и поисковикам с верификацией местности.',
  },
  sector: 'Сектор: Орел — Мценск',
  pins: [
    { id: 'a-14', status: 'found', label: 'Кв. А-14', icon: 'flag', x: 16, y: 20, recordId: 'a-14' },
    { id: 'v-12', status: 'confirmed', label: 'В-12 • Выс. 214', icon: 'person_search', x: 78, y: 70, recordId: 'v-12' },
  ],
  records: {
    'v-12': {
      id: 'v-12',
      stage: 'Полевая разведка (12-15 мая)',
      square: 'Квадрат № 84-Юг',
      title: 'Неизвестный десантник 9-й воздушно-десантной бригады',
      period: 'Октябрь 1941 г. • Бои на шоссе Орел — Мценск',
      photos: [
        {
          src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAnjoy4fngIxUIPxU9OWAgkmlzPDOezfjrB_2OUsDWlj5pe3wybgPDIKaC5aBFv9sHmUjgQX-W6sQBlzX2xaPfxBZQXjDwU8HqWBPkFDL-atBvPZvFZao_YfUiHj64WDN3vr8Tt6bjX9eZQpXZEJVnhQOoKg5ISlZk8wDtGcmnUXyjojKbPI-oiKf56F5ZAG24QDWcU5pDLGnwznO_en2YKlzsG8-9Zs91O1IspvnMyPg2h4mPwjjyB',
          caption: 'Карта 1941 г.',
        },
        {
          src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuClC9EfG28LKQDhzvWb4n525jz6x3HkqQKj_xJF96m_V-qmjPNdo-gAj1uFoRkgxCgTyqjkizsx2VXJTojC_cg5gclUZa-QyFwJbYs37b7Z0aiS9RHr-6Rvi4B_gVY6YHWE723_KGDSpCh_BfyM9XJEa9U1mHMIYOYnBKK_BjLvSvKS9UkmdPFfAVgklqxDwNFMNosjPPKw8AahDwn0Rye9IRGJq0hx9yHnncJYCu0Vys-BwUe_x0oM',
          caption: 'Полевой сектор',
        },
      ],
      coordinates: '53°14′28″ N, 36°28′12″ E (высота 214)',
      source: 'Книга Памяти Орловской области, Том 5, стр. 182',
      evidence: 'Найден смертный медальон (вкладыш на экспертизе в лаборатории «Солдатский медальон»)',
    },
    'a-14': {
      id: 'a-14',
      stage: 'Ожидает проверки',
      square: 'Квадрат № А-14',
      title: 'Предполагаемая позиция боевого охранения',
      period: 'Осень 1941 г. • Подступы к шоссе Орел — Мценск',
      photos: [],
      coordinates: '53°15′02″ N, 36°26′40″ E',
      source: 'Сообщение местного жителя, требует сверки с картами',
      evidence: 'На поверхности — следы окопа и гильзы; раскопки не проводились',
    },
  },
}

export function fetchLastStand(): Promise<LastStandOverview> {
  return withLatency(OVERVIEW)
}
