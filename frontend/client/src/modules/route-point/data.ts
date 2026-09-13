import { withLatency } from '@/core/mock'

/**
 * Данные окна «Точка маршрута».
 *
 * Пока заглушка из макета. Когда подключим `route_service` и `archive_service`,
 * поменяется только тело `fetchRoutePoint`.
 */

export interface RoutePoint {
  id: string
  step: number
  totalSteps: number
  routeTitle: string
  title: string
  place: string
  verifiedBy: string
  comparison: {
    archiveImage: string
    archiveLabel: string
    modernImage: string
    modernLabel: string
    source: string
  }
  audio: {
    title: string
    author: string
    durationSeconds: number
    /** С какого места продолжить — в макете слушатель уже на 1:24. */
    positionSeconds: number
  }
  quest: {
    points: number
    title: string
    description: string
    /** Фрагменты, по которым ответ засчитывается: «76-мм», «ЗиС-3» — всё это верно. */
    acceptedAnswers: string[]
    success: string
    hint: string
  }
  witness: string
  walkingDistanceMeters: number
  arTarget: string
}

const POINTS: Record<string, RoutePoint> = {
  'kromy-line': {
    id: 'kromy-line',
    step: 2,
    totalSteps: 6,
    routeTitle: 'Кромской рубеж',
    title: 'Рубеж обороны 5-го десантного корпуса',
    place: 'Орловско-Курская дуга, высота 243.0 • 1941 г.',
    verifiedBy: 'Подтверждено отрядом «Высота»',
    comparison: {
      archiveImage:
        'https://lh3.googleusercontent.com/aida-public/AB6AXuCnOwZDfmDA8TrLXQjapE-wcnNiCPJu-Om8S0q4wo5LRFlM_81aXzZxvOsEoQ_eHZGwscMzXITBQPiWI9CynMoR346NAFoXDDkeLJIh1NJMK71Xj_Hj08_tTCfWWyaTHh6Gdr2Tf1Zyk5k1a21agaJijf7C42T3sLgDXLwjQ8hS6vE7jy7AtYK-gXDMpEDFsQqoj1_UmRd_1A48A_lwCne00sUwtNS9uiAjZuznX4agR2ZfgQIp9ulI',
      archiveLabel: '1941 • Архивный кадр',
      modernImage:
        'https://lh3.googleusercontent.com/aida-public/AB6AXuDtLwhtkPJGOwmsS1O8yAwY0SFXag6hniQbIUWTQIWQbqU-m-HyvEilm6yBZJSYCnO3Qd4x2n3IA4NbUpHBohcDYP5u1Sb5Xh30j_BAy3yALKicTD1pVH_DOiRDy0f1ZkV3TxUACdHQ0-BmKjbhBYcdDsxdqlwNgZK873KDqGsuCXXqtuEfsmAF3MHDb_KoLf0_iffpVMh97McMIvoKRe3BYPlgeQGCHXmzBWR0jlBpnCtPFXivQuJV',
      modernLabel: '2024 • Мемориал',
      source: 'Архив ЦАМО РФ, дело №148',
    },
    audio: {
      title: 'Голоса эпохи',
      author: 'Сводка Совинформбюро • Ю. Левитан',
      durationSeconds: 190,
      positionSeconds: 84,
    },
    quest: {
      points: 50,
      title: 'Найди калибр орудия на постаменте',
      description:
        'Внимательно изучи табличку на 76-мм пушке ЗИС-3. Введи номер батареи или отсканируй QR-код постамента, чтобы открыть секретный архив десантников!',
      acceptedAnswers: ['76', 'зис'],
      success: 'Верно! Вы открыли архив батареи лейтенанта Гущина.',
      hint: 'Пока неверно. Подсказка: взгляните на щит орудия!',
    },
    witness:
      '«На рассвете 4 октября десантники приняли бой с передовыми танковыми частями. Позиции удерживали до последнего патрона, прикрывая отход мирного населения к Мценску...»',
    walkingDistanceMeters: 120,
    arTarget: 'окопа',
  },
}

export class PointNotFoundError extends Error {
  constructor() {
    super('Точка маршрута не найдена — возможно, ссылка устарела')
    this.name = 'PointNotFoundError'
  }
}

export async function fetchRoutePoint(pointId: string): Promise<RoutePoint> {
  const point = POINTS[pointId]
  if (!point) {
    await withLatency(undefined)
    throw new PointNotFoundError()
  }
  return withLatency(point)
}
