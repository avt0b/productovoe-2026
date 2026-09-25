import type { UserRole } from '@/core/session'

/**
 * Что рассказываем об устройстве приложения.
 *
 * Тексты держим здесь, а не в разметке: разделов шесть, у каждого свой набор
 * строк, и в шаблоне они превратились бы в простыню, которую страшно править.
 *
 * Иконки — только те, что есть в сабсете шрифта (`scripts/icon-names.txt`):
 * чужое имя вылезет на экран словом, а не картинкой.
 */

export interface Section {
  id: string
  /** Имя роута раздела. Модуля может не быть в сборке — тогда карточка без кнопки. */
  route: string
  icon: string
  title: string
  /** Одна фраза: чем занят раздел. */
  summary: string
  details: string[]
  /** Строка только для семейного и детского режима. */
  familyDetail?: string
  /** Что добавить тому, у кого эта роль: ради этого роль и выдают. */
  roleDetail?: Partial<Record<UserRole, string>>
}

export const SECTIONS: readonly Section[] = [
  {
    id: 'routes',
    route: 'routes',
    icon: 'explore',
    title: 'Маршруты',
    summary: 'Куда пойти рядом и что здесь было',
    details: [
      'Карта мест: памятники, братские могилы, места боёв. Фильтры — по годам войны и по виду места.',
      'Точка маршрута — рассказ, фотография «тогда и сейчас», голос эпохи и AR-подсказка прямо на месте.',
      'Свой маршрут собирается из точек и лежит в «Моих маршрутах».',
    ],
    familyDetail: 'В семейном режиме у точек появляются задания для детей.',
    roleDetail: {
      local_historian: 'Краевед публикует маршруты — их видят все семьи области.',
    },
  },
  {
    id: 'excursions',
    route: 'excursions',
    icon: 'groups',
    title: 'Экскурсии',
    summary: 'Живые встречи с краеведом',
    details: [
      'Ближайшие экскурсии — на карте и списком, запись в карточке.',
      'На месте откройте «Сбор группы» и встряхните телефон рядом с краеведом: так он отметит, что вы пришли.',
      'После сбора группа идёт по карте: видно, где все и куда дальше.',
    ],
    roleDetail: {
      local_historian: 'Краевед объявляет экскурсию сам: место, время, маршрут и сколько мест.',
    },
  },
  {
    id: 'last-stand',
    route: 'last-stand',
    icon: 'verified',
    title: 'Последний бой',
    summary: 'Места гибели бойцов и их проверка',
    details: [
      'Карта мест с честной отметкой стадии: заявлено, проверяется, подтверждено.',
      'Подписка на радиус вокруг дома: рядом отметили место — придёт уведомление.',
    ],
    roleDetail: {
      searcher: 'Поисковик добавляет места и прикладывает к находке документы.',
    },
  },
  {
    id: 'hq',
    route: 'hq',
    icon: 'volunteer_activism',
    title: 'Штаб',
    summary: 'Отряды, сборы и «Выходные с поисковиком»',
    details: [
      'Карта отрядов и того, что им нужно: люди на раскопки, снаряжение, деньги на горючее.',
      'Выезд — набор волонтёров на конкретный день с чек-листом, что взять с собой.',
    ],
    roleDetail: {
      searcher: 'Командир отряда объявляет здесь выезды и сборы от имени отряда.',
    },
  },
  {
    id: 'memory',
    route: 'memory',
    icon: 'auto_awesome',
    title: 'Память',
    summary: 'Народный архив и «Живое фото»',
    details: [
      'Фотография из семейного альбома с рассказом становится записью архива — её проверит краевед или поисковик.',
      '«Живое фото» оживляет портрет бойца: снимок и несколько строк письма превращаются в короткий клип.',
      'Семейный архив остаётся вашим: в общий мемориал попадает только то, что вы открыли сами.',
    ],
    roleDetail: {
      searcher: 'Поисковик и краевед подтверждают чужие записи — от этого зависит доверие к архиву.',
      local_historian: 'Поисковик и краевед подтверждают чужие записи — от этого зависит доверие к архиву.',
    },
  },
  {
    id: 'profile',
    route: 'profile',
    icon: 'account_circle',
    title: 'Профиль',
    summary: 'Роль, значки и настройки',
    details: [
      'Роль решает, что можно делать: семья, поисковик, краевед. Заявку подают здесь, решает администратор платформы.',
      'Значки — за то, что действительно сделано: пройденные маршруты, находки, экскурсии.',
      'Здесь же семейный и детский режим и оповещения о новых местах рядом с домом.',
    ],
  },
]

/** Первым — то, ради чего роль выдана; остальное в обычном порядке. */
const ORDER: Partial<Record<UserRole, readonly string[]>> = {
  searcher: ['last-stand', 'hq', 'memory', 'routes', 'excursions', 'profile'],
  local_historian: ['excursions', 'routes', 'memory', 'last-stand', 'hq', 'profile'],
}

export function sectionsFor(role: UserRole | undefined): Section[] {
  const order = role ? ORDER[role] : undefined
  if (!order) return [...SECTIONS]
  const byId = new Map(SECTIONS.map((section) => [section.id, section]))
  const first = order.flatMap((id) => {
    const section = byId.get(id)
    return section ? [section] : []
  })
  return [...first, ...SECTIONS.filter((section) => !order.includes(section.id))]
}

/** Строки карточки с учётом роли и детского режима — в том порядке, в каком читают. */
export function linesOf(section: Section, role: UserRole | undefined, familyMode: boolean): string[] {
  const roleLine = role ? section.roleDetail?.[role] : undefined
  return [...section.details, ...(roleLine ? [roleLine] : []), ...(familyMode && section.familyDetail ? [section.familyDetail] : [])]
}

export interface TourStep {
  icon: string
  rubric: string
  title: string
  body: string
  /** Под текстом показать список разделов — шаг «где что лежит». */
  sections?: boolean
  /** Кнопка в конце шага: куда идти прямо сейчас. */
  action?: { label: string; route: string }
}

const ROLE_STEP: Record<UserRole, { title: string; body: string }> = {
  family: {
    title: 'Вы здесь как семья',
    body: 'Смотрите маршруты, ходите на экскурсии, добавляете в архив фотографии из своего альбома. Поисковик и краевед — это заявка в профиле: её рассматривает администратор платформы.',
  },
  searcher: {
    title: 'Вы поисковик',
    body: 'Вам открыты места «Последнего боя» и проверка записей архива, а в «Штабе» — выезды и сборы отряда. Остальное приложение работает как для всех.',
  },
  local_historian: {
    title: 'Вы краевед',
    body: 'Вы ведёте маршруты и экскурсии и проверяете записи народного архива. Экскурсия объявляется в разделе «Экскурсии», маршрут — в «Моих маршрутах».',
  },
}

const START: Record<UserRole, { body: string; action: { label: string; route: string } }> = {
  family: {
    body: 'Откройте маршруты рядом с домом и выберите точку — дальше приложение само подскажет, что там было.',
    action: { label: 'Открыть маршруты', route: 'routes' },
  },
  searcher: {
    body: 'Загляните в «Штаб»: там видно, какому отряду сейчас нужны люди и на какой день объявлен ближайший выезд.',
    action: { label: 'Открыть «Штаб»', route: 'hq' },
  },
  local_historian: {
    body: 'Посмотрите ближайшие экскурсии: свою объявляют там же, кнопкой в правом верхнем углу списка.',
    action: { label: 'Открыть экскурсии', route: 'excursions' },
  },
}

export function tourSteps(role: UserRole | undefined, familyMode: boolean): TourStep[] {
  const actual = role ?? 'family'
  const steps: TourStep[] = [
    {
      icon: 'auto_stories',
      rubric: 'Маршруты победы',
      title: 'Память рядом с домом',
      body: 'Приложение показывает, что было на ваших улицах в 1941–1945: маршруты по местам боёв, экскурсии с краеведами, народный архив и помощь поисковым отрядам.',
    },
    {
      icon: 'explore',
      rubric: 'Где что лежит',
      title: 'Пять разделов внизу',
      body: 'Нижняя панель — это всё приложение. Каждый раздел про своё; шестой, профиль, — про вас.',
      sections: true,
    },
    { icon: 'badge', rubric: 'Роли', ...ROLE_STEP[actual] },
  ]

  if (familyMode) {
    steps.push({
      icon: 'family_restroom',
      rubric: 'Детский режим',
      title: 'Включён семейный и детский режим',
      body: 'У точек маршрута появляются задания для детей, а тяжёлые подробности поданы мягче. Выключается в профиле, в настройках.',
    })
  }

  steps.push({ icon: 'near_me', rubric: 'Первый шаг', title: 'С чего начать', ...START[actual] })
  return steps
}
