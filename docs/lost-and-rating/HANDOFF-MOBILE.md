# Мобилка «Я потерялся» и рейтинг краеведов: передача дел

Ты продолжаешь работу над клиентом «Маршруты победы» (`frontend/client`,
Vue 3 + TS strict + Tailwind + Capacitor). Задание — [MOBILE.md](./MOBILE.md),
контракт с бэкендом — [CONTRACT.md](./CONTRACT.md). Бо́льшая часть задания
уже сделана и влита в `develop`. Здесь — что готово, где лежит, что осталось
и на чём можно споткнуться.

Состояние на 26.09.2026, `develop` = `50aa7e5`.

## Первым делом прочитай

1. [MOBILE.md](./MOBILE.md) целиком: разделы «Твоя зона», «Ветки и
   коммиты», «Проверка» и «В конце» действуют и для тебя.
2. [CONTRACT.md](./CONTRACT.md): 1.2–1.6 (тревога, уведомления), 2.2–2.4
   (рейтинг).
3. `frontend/client/README.md` и `frontend/client/DESIGN.md`: как устроены
   модули и фичи и как должны выглядеть экраны.
4. Этот файл до конца, особенно «Грабли».

## Что уже в `develop`

| PR | Ветка | Что |
|---|---|---|
| #104, #105 | (бэкенд, не наши) | ручки тревоги и рейтинга в `search_hq_service` |
| [#106](https://github.com/avt0b/productovoe-2026/pull/106) | `feat/mobile-lost-alert` | часть A: A1–A6, **кроме A4.4 «Не вижу…»** |
| [#107](https://github.com/avt0b/productovoe-2026/pull/107) | `feat/mobile-guide-rating` | часть B: B1–B4 полностью |

На объединённом `develop` проверены `npm run typecheck` и `npm run build`,
оба без ошибок. **В браузере никто ничего не прогонял, скриншотов нет, на
живом бэкенде не проверено, шрифт иконок не пересобран.** Это и есть твоя
работа (ниже по порядку).

### Карта файлов: часть A, «Я потерялся»

```
src/features/lost-alert/
  api.ts                 типы по CONTRACT 1.3 и все ручки: raiseLost, fetchActiveAlerts,
                         fetchAlert, respondAlert, resolveAlert, cancelAlert, reportMyPosition.
                         Каждая функция начинается с `if (MOCK) return mock.x(...)`
  mock.ts                тревоги в памяти; tick() двигает потерявшегося на ±5 м, откликнувшихся
                         на ~15 м к нему; мама откликается сама через 20 с; «ошибка» в message
                         → ApiError 409
  useActiveLostAlerts.ts опрос /lost-alerts/active каждые 10 с (только с аккаунтом и при видимой
                         вкладке), автооткрытие экрана с вибрацией; какие тревоги уже открывали,
                         лежит в localStorage `marshruty.lost.opened`
  LostAlertBanner.vue    красная плашка через Teleport, z-index 1400 (ниже NotificationBanner 1500)
  index.ts               единственная точка входа фичи
src/modules/lost/
  index.ts               роут /lost/:alertId, name `lost-alert`, layout bare
  useLostAlert.ts        опрос тревоги каждые 3 с и отправка своей точки каждые 3 с; 409 от
                         reportMyPosition глотается; флаг offline, routeGoal, respondAndGo/
                         resolve/cancel/back; тип LostAlertController
  LostAlertPage.vue      карта + нижняя панель по роли
  format.ts              timeAgo
  components/WatcherPanel.vue  «Иду искать», «Нашлись!», список ищущих
  components/LostPanel.vue     «Вас ищут», в семейном режиме маршрут по кнопке, в обычном сам
                               (watchEffect); «Отбой» через ConfirmAction
  components/ClosedPanel.vue   «Нашлись! Все вместе» / «Отбой»
```

Точечные правки вне зоны фич:

- `features/point-route/usePointRoute.ts`: `moveTarget(point)` и `routedTo`.
  Маршрут перестраивается и тогда, когда уходит цель, а не только когда
  идёшь ты. Совместимо со старыми вызовами: `start`/`stop` работают как
  раньше.
- `features/notifications/useNotificationWatcher.ts`: у вида появилось поле
  `banner?: boolean`; добавлены виды `lost_alert`, `lost_alert_searching`,
  `lost_alert_responding` (у всех трёх `banner: false`, экран открывает сама
  фича), `lost_alert_closed` и `rate_excursion` (ведёт на экскурсию с `?rate=1`).
- `App.vue`: одна строка `<LostAlertBanner />`.
- `env.d.ts`: `VITE_MOCK_NEW_API`, `VITE_MOCK_LOST_ROLE`.
- `modules/excursions/data.ts`: `GroupMember.lost_alert_id?`.
- `modules/excursions/WalkPage.vue`: кнопка «Я потерялся» (ConfirmAction,
  только участнику и только при `status === 'walking'`), красные метки
  `lost:<alertId>`, по нажатию на метку открывается `lost-alert`.
- `scripts/icon-names.txt`: добавлены `sos`, `directions`, `directions_run`,
  `leaderboard`. Сам шрифт **не пересобран** (задача 3).

### Карта файлов: часть B, рейтинг

```
src/features/guide-rating/
  api.ts         fetchLeaderboard (с auth, если есть аккаунт: для `me`), fetchGuideCard,
                 fetchGuideExcursions; типы GuideRank, GuideLeaderboard, GuideCard…
  mock.ts        8 краеведов, байесовское среднее с C = 5; период «месяц» делит счётчики
                 пополам; вошедшему g-petr отдаётся с is_me; неизвестный id → карточка лидера
  format.ts      formatRating, placeLabel
  StarRow.vue, PersonAvatar.vue (аватар ЧУЖОГО человека; UserAvatar только для текущего)
src/modules/guides/
  index.ts                 роуты `guides` (/guides) и `guide` (/guides/:guideId)
  GuidesRatingPage.vue     SegmentTabs период, пьедестал, список, «Это вы», «Показать ещё»
  GuidePage.vue            карточка краеведа: распределение оценок, отзывы, экскурсии
src/modules/excursions/components/TopGuidesStrip.vue   полоска топа на вкладке «Ближайшие»
src/modules/excursions/components/GuideRatingBadge.vue ссылка в карточку, если есть роут `guide`
src/modules/excursions/ExcursionPage.vue   ?rate=1 один раз открывает оценку и убирает параметр
src/modules/profile/components/GuideRankCard.vue       место краеведа в профиле
src/modules/profile/ProfilePage.vue        одна вставка GuideRankCard для роли local_historian
```

## Окружение на этой машине

- **Системного Node нет.** Стоит локальный, в `~/.local/nodejs`, v24. В
  каждой команде сначала:
  ```bash
  export PATH="$HOME/.local/nodejs/bin:$PATH"
  ```
  `node_modules` в `frontend/client` уже установлены. Если их нет, запусти
  `npm ci`.
- `frontend/client/.env.local` не в git и уже лежит на машине:
  ```
  VITE_MOCK_NEW_API=true
  VITE_MOCK_LOST_ROLE=watcher      # или lost
  ```
  После смены роли перезапусти dev-сервер: Vite читает env только на старте.
- **Заглушки закрывают только новые ручки** (тревога и рейтинг). Вход,
  экскурсии, сбор и прогулка ходят в настоящие сервисы. Поэтому даже для
  прогона на заглушках нужен поднятый бэкенд: `docker-compose.yml` в корне
  репозитория или сервисы по одному, как в `backend/README.md`. Адреса
  по умолчанию зашиты в `src/core/server.ts` (`127.0.0.1:8001` auth,
  `:8002` users, `:8004` hq), для локального бэкенда в `.env.local` их
  прописывать не нужно.
- Превью. `.claude/` в `.gitignore`, файл создаёшь локально,
  `.claude/launch.json` в корне репозитория:
  ```json
  {
    "version": "0.0.1",
    "configurations": [
      {
        "name": "client",
        "runtimeExecutable": "npm",
        "runtimeArgs": ["run", "dev", "--prefix", "frontend/client", "--", "--host", "127.0.0.1", "--port", "5174"],
        "port": 5174
      }
    ]
  }
  ```
  Без `--host 127.0.0.1` Vite слушает только IPv6, и браузерная панель его
  не видит. Запуск через `preview_start`, размеры 375×812 и 375×667.
- Проверки: `cd frontend/client && npm run typecheck && npm run build`.
- git и GitHub: `gh` авторизован как `ostrix05`, есть права на запись,
  git-личность `ostrix05 <oovv93568@gmail.com>` уже настроена.
  **`gh pr edit` на gh 2.46 падает** с GraphQL-ошибкой про Projects
  classic. Описание PR правь так:
  ```bash
  gh api -X PATCH repos/avt0b/productovoe-2026/pulls/<N> -F body=@/путь/к/body.md
  ```
  Мерж, если человек сам попросил:
  `gh api -X PUT repos/avt0b/productovoe-2026/pulls/<N>/merge -f merge_method=merge`.
- **Команда мержит в `develop` часто.** Перед любой работой:
  `git fetch origin`, ветка от свежего `origin/develop`, перед пушем
  `git rebase origin/develop`.

## Что осталось: по порядку

### 1. Прогон на заглушках в браузере и скриншоты

Сценарии перечислены в MOBILE.md, раздел «Проверка», п. 4–5. Коротко:

- **watcher**: вход, экран тревоги открылся сам, «Иду искать», маршрут
  строится и перестраивается, «Нашлись!», экран «Нашлись! Все вместе»,
  «К карте группы». Уйди с экрана при активной тревоге: должна появиться
  красная плашка сверху, и по ней ты вернёшься обратно.
- **lost** (перезапусти dev с `VITE_MOCK_LOST_ROLE=lost`): прогулка (нужна
  настоящая экскурсия в статусе `walking`, см. п. 4), «Я потерялся»,
  подтверждение, «Вас ищут», примерно через 20 с «Мама идёт к вам». В
  семейном режиме маршрут строится только по кнопке, в обычном сам.
  «Отбой» с подтверждением.
- **ошибка**: в заглушке подпись с «ошибка» роняет `raiseLost`. WalkPage
  сейчас `message` не передаёт вовсе (`reportLost` в `WalkPage.vue`). Для
  проверки временно добавь `message: 'ошибка'` в `body` и убедись, что
  показан текст `detail`, **но не коммить это**.
- **рейтинг**: оба периода, «Показать ещё», пустое состояние, ошибка,
  переход в карточку, полоска в «Экскурсиях», плашка на экскурсии ведёт в
  карточку, `?rate=1` открывает оценку, карточка в профиле краеведа.
- **регресс**: в «Маршрутах» и «Последнем бое» «Начать маршрут» работает
  как раньше (`usePointRoute` правили).

Каждый найденный баг чини в отдельной ветке от `develop`, например
`fix/mobile-lost-rating-qa`, и открывай отдельный PR. Скриншоты ключевых
экранов положи в описание PR или отдай человеку.

### 2. A4.4 «Не вижу…» (единственный несделанный пункт задания)

Спецификация: MOBILE.md, A4 п. 4; CONTRACT 1.2–1.3 (`kind: "reported"`) и
коды ошибок `raiseLost`. Ветка `feat/mobile-lost-not-seen` от `develop`.

- В `WalkPage.vue` рядом с «Я потерялся» поставь кнопку `Не вижу…` с иконкой
  `person_search` (она уже есть в сабсете). Кнопку видят **и участник, и
  краевед**, но только при `walk.status === 'walking'`. Сейчас
  `canRaiseLost` исключает краеведа, поэтому для новой кнопки заведи
  отдельный computed.
- Кнопка открывает `SheetDialog` со списком, кого можно искать:
  - **участнику** показывай семью: `GET 'users' /family-links/mine`, поля
    `member_id`, `display_name`, `avatar_url`, себя исключи. Функция и тип
    уже есть в `modules/profile/data.ts` (`familyMembers`), **но модули не
    импортируют друг друга**. Вызов делай в фиче: добавь в
    `features/lost-alert/api.ts` свою маленькую функцию с тем же запросом.
  - **краеведу** показывай только отметившихся участников:
    `GET 'hq' /excursions/{id}/participants` (`user_id`, `checked_in_at`,
    бери записи с `checked_in_at !== null`). Это тот же модуль `excursions`,
    так что `fetchParticipants` из `modules/excursions/data.ts` можно
    вызывать прямо в WalkPage. Имена подтягивай одним запросом
    `GET 'users' /profiles/batch?ids=a,b,c` (публичный, CONTRACT, раздел
    про profiles/batch).
- Когда человек выбран, вызывай
  `raiseLost(excursionId, { lost_user_id, lat, lon, accuracy_m })` и
  открывай `lost-alert` с `id` из ответа. Позиция берётся так же, как у
  «Я потерялся».
- Ошибки показывай **внутри листа** (`InlineNotice`), лист не закрывай:
  `404 Этого человека нет в группе`, `403 Искать можно только членов своей
  семьи`, остальное через `errorText`.
- В заглушке `mock.ts` сейчас любая тревога получает `kind: 'self'`. Нужно:
  если в `body` есть `lost_user_id`, создавать `kind: 'reported'`, где
  `my_role: 'watcher'`, я сразу `responding: true` (по контракту поднявший
  считается откликнувшимся), потерявшийся — выбранный человек; неизвестный
  id → `ApiError(404, 'Этого человека нет в группе')`. Пустые списки семьи
  или участников в листе покажи через `StateBlock`.
- Для потерявшегося при `kind === 'reported'` длинная вибрация и
  автооткрытие уже сделаны в `useActiveLostAlerts.ts`. Проверь, что это
  срабатывает.

### 3. Иконки в APK

```bash
cd frontend/client && sh scripts/update-fonts.sh
```

Скрипт качает сабсет Material Symbols с Google Fonts, поэтому нужна сеть.
Без этого в APK вместо значков будут слова «sos», «leaderboard» и т. п. (в
вебе с dev-сервера этого не видно, не обманись). Закоммить
`public/fonts/*` вместе с `icon-names.txt`. Если добавишь новую иконку,
сначала допиши её в список (в алфавитном порядке), потом запускай скрипт.

### 4. Живой бэкенд

Ручки уже в `develop` (`backend/search_hq_service/api/routers/lost_alerts.py`,
`guides.py`, тесты `test_lost_alerts.py`, `test_guide_leaderboard.py`).
Выключи заглушки (`VITE_MOCK_NEW_API=false` или убери строку) и пройди те же
сценарии. Для тревоги нужны три аккаунта и два браузера или два телефона
(MOBILE.md, «Проверка», п. 6): краевед, «мама» и «Маша», связанные семьёй
через код в профиле. Дальше: экскурсия, обе записываются, сбор, бамп, «Маша»
жмёт «Я потерялся». Расхождения с контрактом не подгоняй молча: опиши их и
предложи правку `CONTRACT.md`.

### 5. Отчёт человеку

MOBILE.md, раздел «В конце»: что сделано по A1–A6 и B1–B4, что проверено на
заглушках, а что на живом бэкенде, скриншоты. Назови ограничение: без FCM
тревога приходит, только пока приложение открыто.

## Грабли, на которые уже наступили

- **Зона.** Не трогай `mobile/**` и `src/features/ar/**` (AR и Android,
  это не твоё), папки онбординга, `src/core/**`, `modules/auth/**`,
  `package.json`. В `ProfilePage.vue` допустимы только однострочные вставки.
  Перед коммитом проверь `git status --short`: ни одного файла вне зоны.
- **Модули не импортируют друг друга.** Общее живёт в `src/features/*` и
  импортируется только через `index.ts` фичи. Ссылку на чужой экран делай
  по имени роута под `router.hasRoute('…')`.
- **ref внутри объекта-пропса** (например, `LostAlertController`, который
  передаётся в панели) в шаблоне **не разворачивается**: пиши
  `ctrl.alert.value`, а не `ctrl.alert`. На этом уже ловили ошибки типов.
- `StateBlock` не принимает проп `detail`, только те, что объявлены в
  `ui/StateBlock.vue`. Смотри сигнатуры в самих компонентах, а не по
  памяти.
- `ConfirmAction` сам делает оба шага (кнопка, потом подтверждение).
  Оборачивать его в свой диалог не нужно.
- Новых npm-зависимостей не добавляй. Цвета бери только из токенов
  Tailwind, hex не пиши.
- Коммиты: префикс `feat(client): …` или `fix(client): …`. Комментарии
  по-русски и только там, где решение неочевидно, объясняй «почему».
- Одна часть — одна ветка — один PR в `develop`. **Мержит человек**, если
  прямо не попросил тебя.
- Не пиши в PR «проверено в браузере», если не проверял. Раздел проверки в
  описании PR должен честно говорить, что сделано, а что нет.
