# Мобилка: «Я потерялся» и рейтинг краеведов

Ты делаешь **только мобильное приложение** (`frontend/client`: Vue 3 + TS +
Tailwind + Capacitor) для двух фич проекта «Маршруты победы». Бэкенд
параллельно пишет другой человек по [BACKEND.md](./BACKEND.md). Вы
встречаетесь только в [CONTRACT.md](./CONTRACT.md): ручки, JSON, коды ошибок и
уведомления оттуда — закон.

В мобилке сейчас работают ещё двое:

- **Влад** — нативный AR-модуль в `mobile/` и его обвязку в
  `src/features/ar`. Туда не заходи.
- **Человек с онбордингом и маскотами** — переделывает `src/modules/onboarding`,
  `src/features/onboarding` и вставляет картинки маскотов в дизайн. Эти папки
  не трогай, а общие компоненты `src/ui/**` меняй только в крайнем случае
  (см. «Твоя зона»). Иначе при мерже будут конфликты.

## Первым делом прочитай

1. [CONTRACT.md](./CONTRACT.md) — целиком, два раза. Особенно 1.2 (правила
   тревоги), 1.3 (объект `LostAlert`), 1.6 (уведомления), 2.2–2.4 (рейтинг).
2. `frontend/client/README.md` — как устроены модули (`src/modules`), фичи
   (`src/features`), мета экрана, иконки-сабсет, правила.
3. `frontend/client/DESIGN.md` — дизайн-система. Новые экраны должны выглядеть
   как существующие: токены из `tailwind.config.js`, `MsIcon`, шрифтовые роли
   `font-headline-sm text-headline-sm` и т. п. Не вводи свои цвета в hex.
4. Эталоны вёрстки и кода, на которые опираешься:
   - `src/modules/excursions/WalkPage.vue` + `useWalk.ts` — полноэкранная
     карта, стеклянная тёмная карточка снизу, опрос сервера по таймеру,
     отправка своей точки;
   - `src/features/point-route/usePointRoute.ts` — маршрут до точки;
   - `src/features/notifications/useNotificationWatcher.ts` +
     `NotificationBanner.vue` — опрос уведомлений и плашка поверх экрана;
   - `src/modules/excursions/ExcursionPage.vue`, `ExcursionsPage.vue`,
     `components/GuideRatingBadge.vue`, `components/RateGuideSheet.vue` —
     экскурсии и оценки, которые уже есть;
   - `src/core/api.ts` (`apiRequest`, `ApiError`), `src/core/async.ts`
     (`useAsync`), `src/core/geo` (`useGeolocation`, `distanceKm`,
     `GeoMarker`), `src/core/preferences.ts` (`familyMode`),
     `src/core/format.ts` (`plural`, `formatDate`, `formatDateTime`, `errorText`),
     `src/core/mock.ts` (`withLatency`).
   - Общие компоненты: `ui/geo/GeoMap.vue`, `ui/StateBlock.vue`,
     `ui/SheetDialog.vue`, `ui/ConfirmAction.vue`, `ui/SegmentTabs.vue`,
     `ui/InlineNotice.vue`, `ui/MsIcon.vue`. `ui/UserAvatar.vue` — только
     аватар **текущего** пользователя, для чужих сделаешь свой (ниже).

## Твоя зона

Создаёшь:

```
src/features/lost-alert/**      механика тревоги: api, заглушки, опрос, плашка
src/modules/lost/**             экран тревоги /lost/:alertId
src/features/guide-rating/**    api рейтинга, заглушки, звёзды, аватар человека
src/modules/guides/**           экраны /guides и /guides/:guideId
```

Точечно правишь (только то, что описано в задании):

```
src/modules/excursions/WalkPage.vue, ExcursionsPage.vue, ExcursionPage.vue,
  data.ts, components/GuideRatingBadge.vue, components/TopGuidesStrip.vue (новый)
src/modules/profile/ProfilePage.vue (одна вставка), components/GuideRankCard.vue (новый)
src/features/notifications/useNotificationWatcher.ts (новые виды)
src/features/point-route/usePointRoute.ts (moveTarget — обратно совместимо)
src/App.vue (одна строка — плашка тревоги)
src/env.d.ts (одна переменная — заглушки)
scripts/icon-names.txt + public/fonts/* (новые иконки через update-fonts.sh)
```

Всё остальное — только чтение. Модули не импортируют друг друга: общее
живёт в `src/features/*` и импортируется **только через `index.ts` фичи**.
Ссылка на экран другого модуля — по имени роута с проверкой
`router.hasRoute(...)`: нет модуля — нет ссылки, а не падение.

Новых npm-зависимостей не добавляй.

## Ветки и коммиты

- `feat/mobile-lost-alert` от `origin/develop` — часть A.
- `feat/mobile-guide-rating` от `origin/develop` — часть B. Ветки независимы,
  PR в `develop` по отдельности.
- Коммит на каждый законченный кусок, префикс `feat(client): …`. Перед
  коммитом `git status --short` — ни одного файла вне зоны.
- Комментарии по-русски и только там, где решение неочевидно: объясняют
  «почему», а не пересказывают код (посмотри, как это сделано в
  `useWalk.ts` и `GeoMap.vue`).
- Мержит человек. Ты пушишь ветку и открываешь PR с описанием и проверкой.

## Работа до готовности бэкенда: заглушки

Бэкенд появится позже, ждать его нельзя. Поэтому:

1. В `src/env.d.ts` в `ImportMetaEnv` добавь:
   ```ts
   /** `true` — ручки «Я потерялся» и рейтинга отвечают заглушками (пока бэкенд не готов). */
   readonly VITE_MOCK_NEW_API?: string
   /** Роль в заглушке тревоги: `lost` — я потерялся, `watcher` — я ищу. По умолчанию `watcher`. */
   readonly VITE_MOCK_LOST_ROLE?: string
   ```
2. В каждой фиче `api.ts` каждая функция начинается с
   `if (MOCK) return mock.<то же>(...)`, где
   `const MOCK = import.meta.env.VITE_MOCK_NEW_API === 'true'`. Заглушки лежат
   в `mock.ts` той же фичи и отвечают через `withLatency` из `core/mock.ts`,
   чтобы были видны состояния загрузки.
3. Заглушки собери **из примеров JSON контракта** — тогда переход на
   настоящий бэкенд — это просто выключить флаг.
4. Локально: `frontend/client/.env.local` (не в git) с
   `VITE_MOCK_NEW_API=true`. Когда бэкенд смержат, флаг выключается, код
   заглушек остаётся (удобно для демо и тестов).

Требования к заглушке тревоги (`features/lost-alert/mock.ts`), чтобы можно
было прогнать весь сценарий в браузере:

- состояние в памяти модуля (`let alerts: LostAlert[]`);
- `VITE_MOCK_LOST_ROLE=watcher`: `fetchActiveAlerts()` сразу возвращает одну
  тревогу `kind: "self"`, `my_role: "watcher"` (как в CONTRACT 1.3), чтобы
  сработало автоматическое открытие экрана;
- `VITE_MOCK_LOST_ROLE=lost`: активных тревог нет, пока не нажмёшь «Я
  потерялся»; `raiseLost()` создаёт тревогу с `my_role: "lost"` и двумя
  ищущими (мама — семья, краевед — `guide`), позиции — рядом с Орлом;
- каждый `fetchAlert()` чуть сдвигает точку потерявшегося (±5 м) и
  приближает откликнувшихся ищущих к нему на ~15 м, пересчитывает
  `distance_m`; через ~20 секунд после создания заглушка «откликает» маму,
  чтобы у потерявшегося было видно «Мама идёт к вам»;
- `respondAlert`/`resolveAlert`/`cancelAlert` меняют состояние по правилам
  контракта и возвращают тревогу;
- ошибку тоже можно увидеть: `raiseLost` бросает `new ApiError(409, 'Потеряться можно только во время прогулки группы')`,
  если в `message` передано слово `ошибка`.

---

## Часть A. «Я потерялся»

### Что должно получиться (сценарий глазами людей)

1. Семья на прогулке с краеведом (экран `WalkPage`, `/excursions/:id/walk`).
   Маша отстала и жмёт «Я потерялся», подтверждает.
2. Её телефон открывает экран тревоги `/lost/:alertId`: «Вас ищут», кто
   получил тревогу, крупный совет стоять на месте (в семейном режиме) и кнопки
   «Меня нашли» и «Отбой — я не потерялся».
3. У мамы и у краеведа в течение ~10 секунд телефон вибрирует и сам
   открывает экран той же тревоги: где Маша на карте, сколько до неё, когда
   была последняя точка. Мама жмёт «Иду искать», и строится пеший маршрут до
   Маши, который перестраивается, пока обе двигаются.
4. У Маши появляется «Мама идёт к вам · 230 м» и мамина точка на карте.
5. Мама подходит ближе 40 м: «Вы рядом — видите её?» Жмёт «Нашлась!», и у
   всех экран показывает «Нашлись! Все вместе», поиск закрыт.
6. Этап 2: мама не видит Машу рядом (та растерялась и ничего не нажала).
   Мама на карте группы жмёт «Не вижу…», выбирает Машу, и тревога
   поднимается за неё: Маше — «Вас ищут», маме — маршрут до последней точки
   Маши.

### A1. Фича `src/features/lost-alert`

**`api.ts`** — типы ровно по CONTRACT 1.3 и функции:

```ts
export type LostAlertStatus = 'active' | 'found' | 'cancelled' | 'expired'
export type LostAlertKind = 'self' | 'reported'
export type LostAlertRole = 'lost' | 'watcher' | 'observer'

export interface LostPosition {
  lat: number
  lon: number
  accuracy_m: number | null
  updated_at: string
}

export interface LostPerson {
  user_id: string
  display_name: string
  avatar_url: string | null
  is_me: boolean
  position: LostPosition | null
}

export interface LostWatcher {
  user_id: string
  display_name: string
  avatar_url: string | null
  relation: 'family' | 'guide'
  is_me: boolean
  responding: boolean
  responded_at: string | null
  position: LostPosition | null
  distance_m: number | null
}

export interface LostAlert {
  id: string
  excursion_id: string
  excursion_title: string
  status: LostAlertStatus
  kind: LostAlertKind
  my_role: LostAlertRole
  message: string
  lost: LostPerson
  raised_by: { user_id: string; display_name: string }
  watchers: LostWatcher[]
  created_at: string
  resolved_at: string | null
  resolved_by: { user_id: string; display_name: string } | null
}

export interface RaiseLostBody {
  lost_user_id?: string | null
  lat?: number
  lon?: number
  accuracy_m?: number | null
  message?: string
}
```

| Функция | Запрос |
|---|---|
| `raiseLost(excursionId, body): Promise<LostAlert>` | `POST 'hq' /excursions/{id}/lost`, `auth: true` |
| `fetchActiveAlerts(): Promise<LostAlert[]>` | `GET 'hq' /lost-alerts/active`, `auth: true` |
| `fetchAlert(alertId): Promise<LostAlert>` | `GET 'hq' /lost-alerts/{id}`, `auth: true` |
| `respondAlert(alertId)` / `resolveAlert(alertId)` / `cancelAlert(alertId)` | `POST …/respond` / `…/resolve` / `…/cancel`, `auth: true` |
| `reportMyPosition(excursionId, {lat, lon, accuracy_m})` | `PUT 'hq' /excursions/{id}/walk/position`, `auth: true` |

`reportMyPosition` — своя копия, а не импорт из `modules/excursions`: фича
модули не импортирует. Все id — через `encodeURIComponent`, как в
`modules/excursions/data.ts`.

**`useActiveLostAlerts.ts`** — один на всё приложение (заводится в плашке):

- опрос `fetchActiveAlerts()` раз в **10 с**, только если
  `useSessionStore().hasAccount` и `document.visibilityState === 'visible'`;
  при возврате в приложение (`visibilitychange`) — сразу; смена пользователя
  (`session.user?.id`) — сбросить всё и спросить заново. Скопируй скелет из
  `useNotificationWatcher`;
- ошибки сети глотаются: тревога — не повод показывать ошибку на чужом экране;
- **автооткрытие**: появилась активная тревога, которую это устройство ещё не
  открывало, и я в ней ищущий (`my_role === 'watcher'`) или меня ищут
  (`my_role === 'lost' && kind === 'reported'`) → длинная вибрация
  `navigator.vibrate?.([400, 150, 400, 150, 400])` и
  `router.push({ name: 'lost-alert', params: { alertId } })`, если роут есть
  и я уже не на этом экране. Какие id уже открывались, запоминай в
  `localStorage` (ключ `marshruty.lost.opened`, массив id, чтение и запись в
  `try/catch`, как в `core/preferences.ts`): перезапуск приложения не должен
  второй раз выдёргивать человека на уже открытую тревогу;
- наружу: `alerts` (computed), `refresh()`.

**`LostAlertBanner.vue`** — красная плашка сверху поверх любого экрана
(`Teleport to="body"`, `pt-safe`, `z` выше контента, но ниже
`NotificationBanner`; посмотри его стили). Показывается, пока есть активная
тревога и я **не** на её экране:

- я ищущий: `Идёт поиск: «Маша» · 230 м` (расстояние — моё `distance_m`, если есть);
- меня ищут: `Вас ищут — откройте карту`.

Нажатие ведёт на `lost-alert`. Несколько тревог — показывай самую новую и
«+1» справа. Иконка `sos`, фон `bg-error`, текст `text-on-error` (проверь
токены в `tailwind.config.js`).

**`index.ts`** экспортирует: `LostAlertBanner`, `useActiveLostAlerts`, все
функции и типы из `api.ts`.

### A2. `usePointRoute`: цель, которая движется

Сейчас маршрут перестраивается, только когда сдвинулся **сам** человек. В
поиске движется и цель. Добавь в `src/features/point-route/usePointRoute.ts`
обратно совместимое:

```ts
let routedTo: LatLon | null = null
```

- в `reroute()` после успешной постройки `routedTo = { lat: to.lat, lon: to.lon }`;
- условие пропуска в `reroute()` станет таким:

```ts
const walkedAway = !routedFrom || distanceKm(routedFrom, me) * 1000 > REROUTE_AFTER_METERS[mode.value]
// Цель тоже может идти — человек, а не памятник.
const targetMoved = !routedTo || distanceKm(routedTo, to) * 1000 > REROUTE_AFTER_METERS[mode.value]
const tooSoon = Date.now() - routedAt < REROUTE_MIN_INTERVAL_MS
if (!force && route.value && ((!walkedAway && !targetMoved) || tooSoon)) return
```

- новая функция:

```ts
/**
 * Цель сдвинулась (ищем человека, он тоже идёт). Поездка та же: `trip` не
 * растёт, и карта не подгоняет вид заново на каждый его шаг. Маршрут
 * перестроится сам, когда цель уйдёт дальше порога.
 */
function moveTarget(point: RouteTarget): void {
  if (!target.value || target.value.id !== point.id) return start(point)
  target.value = { id: point.id, lat: point.lat, lon: point.lon }
  void reroute()
}
```

- `start()` и `stop()` сбрасывают `routedTo = null`; `moveTarget` верни из
  `usePointRoute`.

Проверь, что «Маршруты» и «Последний бой» (они используют `usePointRoute`)
работают как раньше.

### A3. Экран тревоги: модуль `src/modules/lost`

**`index.ts`**:

```ts
export default defineModule({
  id: 'lost',
  routes: [
    {
      // Полноэкранная карта, как прогулка: шапка и вкладки только мешали бы искать.
      path: '/lost/:alertId',
      name: 'lost-alert',
      component: () => import('./LostAlertPage.vue'),
      props: true,
      meta: { title: 'Поиск', layout: 'bare', tab: 'excursions' },
    },
  ],
})
```

**`LostAlertPage.vue`** (`props: { alertId: string }`). Вёрстка — как
`WalkPage.vue`: карта на весь экран подложкой, сверху круглая «Назад» и
пилюля статуса, снизу тёмная стеклянная карточка
(`bg-night/55 backdrop-blur-md`, те же классы). Разбей на компоненты в
`modules/lost/components/`, чтобы страница не разрослась за ~250 строк.

Логика:

- `useAsync` для первой загрузки `fetchAlert(alertId)`, дальше опрос каждые
  **3 с**, пока экран открыт (`onBeforeUnmount` — очистить таймеры). Сеть
  моргнула — оставляем последнее состояние и показываем мелкую строку
  «Нет связи — показываем последнее известное»;
- `403`/`404` при первой загрузке — `StateBlock` с `detail` из ошибки и кнопкой
  «К экскурсиям»;
- `useGeolocation()` из `core/geo` — `start()` при входе; пока
  `status === 'active'`, каждые **3 с** `reportMyPosition(alert.excursion_id, …)`.
  Ошибку `409` (прогулка закончилась) глотать молча;
- «Назад» — `router.back()`, если есть история, иначе на
  `excursion-walk` этой экскурсии (если роут есть), иначе на `excursions`.
  Уход с экрана тревогу **не** закрывает (плашка сверху вернёт сюда).

Карта (`GeoMap`):

- `markers`:
  - потерявшийся, если `lost.position` есть: `tone: 'primary'`,
    `icon: 'sos'`, `label: display_name`; если он — это я, его не рисуем
    отдельно (меня рисует проп `user`);
  - каждый ищущий с позицией, кроме меня: `tone: 'secondary'`,
    `icon: responding ? 'directions_run' : (relation === 'guide' ? 'record_voice_over' : 'person')`,
    `label: \`${display_name}${responding ? ' · идёт' : ''}\``;
- `user` — моя позиция из `useGeolocation`;
- `paths` — `pointRoute.path`, если маршрут строится;
- `focus` — при первой загрузке показать меня и потерявшегося вместе:
  `{ key: alertId, points: [я, потерявшийся] }`, дальше — `pointRoute.focus`;
- `follow` — пока я иду по маршруту.

Маршрут: `const pointRoute = usePointRoute(geo)`, где `geo` — объект
`{ position, status, start }` от `useGeolocation` (так делает
`RoutesPage.vue`). Цель обновляй через `pointRoute.moveTarget({ id, lat, lon })`
на каждом опросе, пока маршрут включён.

Нижняя карточка по состояниям. Тексты — ровно эти, с учётом семейного
режима (`usePreferencesStore().familyMode`): в нём к потерявшемуся на «ты»,
иначе на «вы».

**Я ищу (`my_role === 'watcher'`), тревога активна:**

- заголовок: `kind === 'self'` → `Потерялся участник: {Имя}`, иначе
  `Ищем участника: {Имя}`; под ним `excursion_title`;
- строка про точку: `Последняя точка — {N} с/мин назад` (из
  `lost.position.updated_at`, обновляется раз в секунду), `± {accuracy} м`; нет
  точки — `«{Имя}» ещё не прислал(а), где находится — спросите у группы`
  (скобки с «(а)» тут допустимы: имя не склоняем);
- `message`, если не пустое, — цитатой: `«Я у фонтана»`;
- не откликнулся: главная кнопка **«Иду искать»** → `respondAlert`, затем
  `pointRoute.start(потерявшийся)`; вторая — «Нашлись!» (см. ниже);
- откликнулся: `Осталось {metersLeft} м` из `pointRoute` (маршрут уже на
  карте, отдельный навигатор не нужен). При
  `pointRoute.state === 'arrived'` (ближе 40 м) карточка меняется на
  `Вы рядом — видите «{Имя}»?` и главная кнопка — **«Нашлись!»**;
- если я открыл экран уже откликнувшимся (перезапуск приложения), маршрут
  включается сам;
- кнопка «Нашлись!» (всегда доступна ищущему, не только рядом) →
  `resolveAlert`;
- список других ищущих мелко: `Мама · идёт · 230 м`, `Краевед · не ответил`.

**Меня ищут (`my_role === 'lost'`), тревога активна:**

- заголовок: семейный режим — `Тебя ищут`, иначе — `Вас ищут`;
- если никто ещё не откликнулся: `Тревога у: {имена ищущих через запятую}. Ждём, кто откликнется.`;
- откликнувшиеся — крупно, по одному: `{Имя} идёт к тебе/вам · 230 м`;
- **семейный режим:** большая карточка-совет
  `Стой на месте и никуда не уходи. {Ближайший} видит тебя на карте и уже идёт.`
  (нет откликнувшихся — `Стой на месте. Взрослые уже знают, что ты потерялся(-ась).`).
  Маршрут сам **не** строим. Вторая кнопка — «Показать дорогу к {ближайшему}»:
  включает маршрут к ближайшему откликнувшемуся;
- **обычный режим:** маршрут к ближайшему откликнувшемуся включается сам (цель
  меняется, когда ближайшим становится другой); нет откликнувшихся — к
  краеведу, если у него есть точка, иначе без маршрута;
- кнопки: **«Меня нашли»** → `resolveAlert`; «Отбой — я не потерялся(-ась)»
  через `ConfirmAction` (`tone="neutral"`,
  `warning="Семья и краевед увидят, что поиск отменён"`) → `cancelAlert`.

**Наблюдатель (`observer`)** — только карта и текст «Вы видите поиск как
администратор», без кнопок.

**Поиск закрыт** (`status !== 'active'`):

- `found`: большой значок `celebration`, `Нашлись! Все вместе`, мелко
  `Отметил(а): {resolved_by.display_name}`;
- `cancelled`: `Отбой тревоги — {Имя} не потерялся(-ась)`;
- `expired`: `Поиск закрыт по времени`;
- кнопка `К карте группы` → `excursion-walk` (если роут есть), иначе `К экскурсиям`;
- таймеры опроса и отправки точки остановить, маршрут `stop()`.

Во время любых действий кнопка показывает `progress_activity` с
`animate-spin` и `disabled`. Ошибка действия — красная строка в карточке
(`errorText(reason)`, как в `WalkPage`), экран не падает.

### A4. Прогулка: кнопка «Я потерялся» и красная метка

`src/modules/excursions/WalkPage.vue`:

1. В `data.ts` у `GroupMember` добавь `lost_alert_id?: string | null`
   (CONTRACT 1.5).
2. Участнику (не краеведу), пока `walk.status === 'walking'`, в нижней
   карточке после кнопок — **«Я потерялся»**: контурная красная кнопка
   (`border-error text-error`, иконка `sos`), по нажатию —
   `ConfirmAction` (`label="Я потерялся"`, `icon="sos"`,
   `warning="Семья и краевед сразу увидят, где вы, и пойдут к вам"`,
   `confirm-label="Да, позвать на помощь"`, `tone="danger"`). Подтвердил —
   `raiseLost(excursionId, { lat, lon, accuracy_m })` с текущей позицией из
   `useWalk().position` (позиции нет — без координат) → `router.push` на
   `lost-alert` с `id` из ответа. Ответ `200` (тревога уже была) — тоже
   просто открыть её.
3. У участников с `lost_alert_id` метка на карте: `tone: 'primary'`,
   `icon: 'sos'`, `label: 'Потерялся'`; нажатие на неё открывает
   `lost-alert` с этим id.
4. **Этап 2 — «Не вижу…»**, делай после всего остального. Кнопка
   `Не вижу…` (иконка `person_search`) рядом с «Я потерялся» — и у
   краеведа тоже. Открывает `SheetDialog` со списком, кого можно искать:
   - участнику — его семья: `GET 'users' /family-links/mine`
     (`member_id`, `display_name`, `avatar_url`), кроме себя;
   - краеведу — отметившиеся участники: `GET 'hq' /excursions/{id}/participants`
     (там `user_id`, `checked_in_at`; берём только отметившихся), имена —
     одним запросом `GET 'users' /profiles/batch?ids=a,b,c` (публичная;
     `display_name`, `avatar_url`).

   Выбрал человека → `raiseLost(excursionId, { lost_user_id, lat, lon, accuracy_m })`
   → экран тревоги. Если человека нет в группе, бэкенд ответит `404
   Этого человека нет в группе` — покажи это в листе.

### A5. Уведомления

В `src/features/notifications/useNotificationWatcher.ts`:

1. В интерфейс `Kind` добавь необязательное `banner?: boolean` (по
   умолчанию `true`). В `toBanner` при `kind.banner === false` верни `null`:
   уведомление остаётся в ленте (`modules/notifications`) и по нажатию ведёт
   куда надо, но плашкой не всплывает.
2. Новые виды в `KINDS`:

| `kind` | `actionLabel` | `icon` | `freshMs` | `target` | `banner` |
|---|---|---|---|---|---|
| `lost_alert` | `Открыть поиск` | `sos` | 2 ч | `{ name: 'lost-alert', params: { alertId: payload.alert_id } }` | `false` — экран открывает сама фича тревоги |
| `lost_alert_searching` | `Открыть карту` | `sos` | 2 ч | то же | `false` |
| `lost_alert_responding` | `Открыть карту` | `directions_run` | 2 ч | то же | `false` — это уже видно на экране тревоги |
| `lost_alert_closed` | `Подробнее` | `celebration` | 1 ч | то же | `true` |
| `rate_excursion` | `Оценить` | `star` | 7 дней | `{ name: 'excursion', params: { excursionId: payload.excursion_id }, query: { rate: '1' } }` | `true` |

Нет нужного поля в `payload` — `target` возвращает `null`, как у
существующих видов.

### A6. Корень приложения

В `src/App.vue` рядом с `<NotificationBanner />` добавь
`<LostAlertBanner />` (импорт из `@/features/lost-alert`) с коротким
комментарием, зачем он в корне. Больше в `App.vue` ничего не меняй.

---

## Часть B. Рейтинг краеведов

### B1. Фича `src/features/guide-rating`

Общая для трёх мест (экран рейтинга, полоска в «Экскурсиях», профиль
краеведа), поэтому это фича, а не модуль.

**`api.ts`**, типы по CONTRACT 2.3–2.5:

```ts
export type RatingPeriod = 'all' | 'month'

export interface GuideRank {
  place: number
  guide_id: string
  display_name: string
  avatar_url: string | null
  city: string
  is_verified: boolean
  average: number
  count: number
  score: number
  excursions_led: number
  last_rated_at: string | null
  is_me: boolean
}

export interface GuideLeaderboard {
  period: RatingPeriod
  global_average: number
  prior_weight: number
  prior_mean: number
  total: number
  items: GuideRank[]
}

export interface GuideReview {
  id: string
  excursion_id: string
  guide_id: string
  rater_id: string
  rating: number
  comment: string
  created_at: string
  rater_name: string
  rater_avatar_url: string | null
  excursion_title: string
}

export interface GuideCard {
  guide_id: string
  average: number
  count: number
  recent: GuideReview[]
  score: number | null
  place: number | null
  total_ranked: number
  excursions_led: number
  distribution: Record<'1' | '2' | '3' | '4' | '5', number>
  profile: {
    display_name: string
    avatar_url: string | null
    city: string
    role: string
    is_verified: boolean
  } | null
}

/** Ближайшая экскурсия краеведа — только то, что нужно карточке. */
export interface GuideExcursion {
  id: string
  title: string
  place_name: string
  starts_at: string
  status: string
}
```

| Функция | Запрос |
|---|---|
| `fetchLeaderboard(period, { limit = 50, offset = 0 } = {})` | `GET 'hq' /guides/rating?period=&limit=&offset=`; `auth: true`, если `session.hasAccount` (для `is_me`), иначе без токена |
| `fetchGuideCard(guideId)` | `GET 'hq' /guides/{id}/rating` |
| `fetchGuideExcursions(guideId)` | `GET 'hq' /excursions?guide_id=&upcoming_only=true`, из ответа взять поля `GuideExcursion` |

Плюс `mock.ts` (8 краеведов с разным числом оценок, чтобы было видно, что
одна пятёрка ниже двадцати оценок 4,8; карточка по контракту) и
переключение через `VITE_MOCK_NEW_API`, как в части A.

**Компоненты фичи:**

- `StarRow.vue` — `props: { value: number; size?: number }`: пять
  `MsIcon` `star` / `star_half` / `star_border`. Логику округления возьми из
  `GuideRatingBadge.vue` (`>= n − 0.25` — полная, `>= n − 0.75` — половина).
  `aria-label="Оценка 4,8 из 5"`.
- `PersonAvatar.vue` — `props: { name: string; url: string | null; size?: number }`:
  картинка по `url` (с `alt`), при отсутствии или ошибке загрузки — кружок с
  первой буквой имени на `bg-secondary-container`.
- `formatRating(value)` — `4.83 → "4,8"` (одна цифра после запятой, запятая).
- `placeLabel(place)` — `1 → "1-е место"`.

`index.ts` экспортирует всё это.

### B2. Модуль `src/modules/guides`

```ts
export default defineModule({
  id: 'guides',
  routes: [
    {
      path: '/guides',
      name: 'guides',
      component: () => import('./GuidesRatingPage.vue'),
      meta: { title: 'Рейтинг краеведов', layout: 'detail', tab: 'excursions', public: true },
    },
    {
      path: '/guides/:guideId',
      name: 'guide',
      component: () => import('./GuidePage.vue'),
      props: true,
      meta: { title: 'Краевед', layout: 'detail', tab: 'excursions', public: true },
    },
  ],
})
```

**`GuidesRatingPage.vue`:**

- `SegmentTabs` «За всё время» (`value: 'all'`, иконка `emoji_events`) /
  «За месяц» (`'month'`, `calendar_month`); смена периода перезагружает.
- `useAsync` + `StateBlock` (загрузка, ошибка с «Повторить», пусто:
  `emptyIcon="emoji_events"`,
  `emptyText="Пока никто не оценил краеведов — оценки появятся после первых экскурсий"`).
- Первые три места — «пьедестал»: три карточки в ряд (второе место слева,
  первое по центру и выше, третье справа), крупный `PersonAvatar`, имя,
  `StarRow`, `4,9 · 23 отзыва`. Цвет номера места — токены
  (`tertiary` для первого и т. п., подбери из палитры, не hex).
- Остальные — список строк: номер места, `PersonAvatar`, имя + `verified`
  (если `is_verified`), город, `StarRow` мелко,
  `4,9 · 23 отзыва · 12 экскурсий` (через `plural` из `core/format`).
- Своя строка (`is_me`) подсвечена и подписана «Это вы».
- Внизу «Показать ещё», если `items.length < total`: следующая страница с
  `offset`.
- Под переключателем — сворачиваемый `InlineNotice` (`tone="info"`,
  `icon="info"`) «Как считаем места»:
  `Место зависит и от оценки, и от числа отзывов: одна пятёрка не обгонит сорок оценок по 4,8. Считаем только оценки тех, кто действительно был на экскурсии.`
- Нажатие на краеведа → `{ name: 'guide', params: { guideId } }`.

**`GuidePage.vue`** (`props: { guideId: string }`):

- `fetchGuideCard` и `fetchGuideExcursions` параллельно; ошибка второго не
  ломает экран (просто нет блока экскурсий).
- Шапка: большой `PersonAvatar`, имя (нет профиля — «Краевед»), город,
  значок «Подтверждённый краевед» при `is_verified`.
- Блок оценки: крупно `4,9`, `StarRow`, `23 отзыва`, чип `1-е место из 12`
  (ведёт на `guides`); нет оценок — `Пока без оценок — оценить краеведа
  можно после экскурсии с ним`.
- Распределение: пять строк 5→1 с полосками, ширина — доля от `count`.
- `Провёл(а) экскурсий: 12`.
- «Ближайшие экскурсии»: карточки (название, `formatDateTime(starts_at)`,
  `place_name`) → `{ name: 'excursion', params: { excursionId } }`, если роут
  есть; пусто — блок не показывать.
- «Отзывы»: `recent` — `PersonAvatar` + `rater_name`, `StarRow`,
  `excursion_title`, `formatDate(created_at)`, `comment` (если не пустой).

### B3. Экскурсии

`src/modules/excursions/`:

1. **`components/TopGuidesStrip.vue`** (новый): горизонтальная прокрутка
   (`overflow-x-auto`, `snap-x`) из топ-5 `fetchLeaderboard('all', { limit: 5 })`:
   карточка ~`w-36` — `PersonAvatar`, имя (`truncate`), `StarRow` + `4,9`,
   `23 отзыва`; последняя карточка «Весь рейтинг» → `guides`. Заголовок
   блока `Лучшие краеведы`. Ошибка или пустой рейтинг — блок не
   показывается вовсе (не захламлять главный экран); загрузка — три серые
   заглушки-карточки. Нет роута `guides` — блок не показывается.
2. **`ExcursionsPage.vue`**: вставь `<TopGuidesStrip v-if="tab === 'upcoming'" />`
   между шапкой-секцией и переключателем «Ближайшие/Мои».
3. **`data.ts`**: у `GuideRatingSummary` добавь необязательные поля из
   CONTRACT 2.4 (`place?`, `total_ranked?`, `profile?` и т. д.) —
   необязательные, чтобы старый бэкенд не ломал типы.
4. **`components/GuideRatingBadge.vue`**: вся плашка — `RouterLink` на
   `{ name: 'guide', params: { guideId } }` (новый проп `guideId`, если роута
   нет — остаётся простым блоком); показывает имя краеведа из
   `summary.profile.display_name` вместо слова «Краевед», если оно есть, и
   чип `{place}-е место`, если `place` есть; справа `chevron_right`. В
   `ExcursionPage.vue` передай `:guide-id="excursion.guide_id"`.
5. **`ExcursionPage.vue`**: пришли с `?rate=1` (из уведомления
   `rate_excursion`) — после загрузки экскурсии, если `canRate`, открой
   `sheet = 'rate'` и убери `rate` из адреса через `router.replace`, чтобы
   «Назад» и обновление не открывали лист снова.

### B4. Профиль краеведа

`src/modules/profile/components/GuideRankCard.vue` (новый) и одна вставка в
`ProfilePage.vue` — только для `session.user?.role === 'local_historian'`
(рядом с блоком ролей; найди место, не ломая порядок остальных секций).
Карточка берёт `fetchGuideCard(session.user.id)`:

- есть оценки: `Ваш рейтинг` — `4,8`, `StarRow`, `1-е место из 12 · 14 отзывов`,
  кнопка `Моя карточка` → `guide`;
- нет оценок: `Пока нет оценок — проведите экскурсию, и участники смогут вас оценить`;
- ошибка — карточка не показывается.

Файл `ProfilePage.vue` может параллельно трогать человек с маскотами:
вставка должна быть одной строкой импорта и одной строкой в шаблоне.

---

## Иконки

Новые имена, которых нет в сабсете: `sos`, `directions_run`, `leaderboard`
(если используешь). Допиши их в `scripts/icon-names.txt` (это одна строка
через запятую, держи алфавитный порядок) и выполни:

```bash
cd frontend/client && sh scripts/update-fonts.sh
```

Без этого вместо значка в APK будет слово «sos». Используешь ещё какую-то
иконку — проверь, что она есть в списке.

## Проверка

1. `cd frontend/client && npm run typecheck` — без ошибок (обязательно).
2. `npm run build` — собирается.
3. Превью в браузере: `.claude/launch.json` с конфигурацией
   `npm run dev --prefix frontend/client -- --host 127.0.0.1 --port 5174`
   (без `--host` Vite слушает только IPv6, и браузерная панель его не
   видит), запуск через `preview_start`. Размеры 375×812 и низкий 375×667.
4. На заглушках (`VITE_MOCK_NEW_API=true`) пройди:
   - `VITE_MOCK_LOST_ROLE=watcher`: вход → экран сам открылся на тревоге →
     «Иду искать» → маршрут строится и перестраивается → «Нашлись!» →
     экран «Нашлись! Все вместе» → «К карте группы». Уход с экрана при
     активной тревоге → красная плашка сверху → возвращает на экран;
   - `VITE_MOCK_LOST_ROLE=lost`: прогулка → «Я потерялся» → подтверждение →
     «Вас ищут» → через ~20 с «Мама идёт к вам» → в семейном режиме маршрута
     нет, по кнопке — есть; в обычном — сам → «Отбой» с подтверждением;
   - ошибка `raiseLost` показывается текстом из `detail`;
   - рейтинг: оба периода, «Показать ещё», пусто, ошибка, переход в
     карточку, полоска в «Экскурсиях», плашка на экскурсии ведёт в карточку,
     `?rate=1` открывает оценку, карточка в профиле краеведа.
5. «Маршруты» и «Последний бой» — «Начать маршрут» работает как раньше
   (ты трогал `usePointRoute`).
6. Когда бэкенд смержат в `develop`: выключи заглушки и пройди то же на
   живом стенде. Для «Я потерялся» нужны два телефона (или два браузера) и
   три аккаунта:
   - краевед;
   - «мама» и «Маша», связанные семьёй: приглашение в профиле, раздел
     «Семья», код;
   - экскурсия краеведа → обе записываются → краевед открывает сбор → бамп
     каждой → краевед ведёт группу → «Маша» жмёт «Я потерялся».

## В конце

Отчёт человеку: что сделано по пунктам A1–A6 и B1–B4, что сознательно не
делал и почему, где отступил от контракта (не должен — если пришлось,
опиши и предложи правку `CONTRACT.md`), что проверено на заглушках и что на
живом бэкенде, скриншоты ключевых экранов. Ограничение, которое стоит
назвать: без FCM тревога приходит, только пока приложение открыто.
