# Дизайн-система мобильного клиента «Маршруты победы»

Эталон — экран входа `src/modules/auth/AuthPage.vue`. Он уже собран по этим
правилам. Сомневаешься, как что-то должно выглядеть, — открой его и повтори
приём, а не изобретай свой.

Токены живут в `tailwind.config.js`, анимации и глобальные слои — в
`src/style.css`. Произвольных `#hex`, шрифтов и теней в разметке быть не должно:
нет подходящего токена — значит, приём выбран неверный.

## 1. Палитра: чем что красим

| Роль | Токены | Где применяем |
| --- | --- | --- |
| **primary** — приглушённый кумач | `primary`, `primary-container`, `on-primary` | главное действие экрана, активная метка на карте, акцент заголовка. Один главный акцент на экран, не больше |
| **secondary** — полевая олива | `secondary`, `secondary-container`, `on-secondary-container` | поисковая и полевая тема: отряды, выезды, «идёт сбор», успешные статусы |
| **tertiary** — латунь и охра | `tertiary`, `tertiary-container`, `tertiary-fixed`, `on-tertiary-fixed` | наградное и подтверждённое: значки, «Подтверждено архивом», достижения |
| **surface / parchment** | `surface`, `surface-container-lowest…highest`, `bg-parchment` | лист, на котором лежит приложение, и карточки на нём |
| **ink** | `on-surface`, `on-surface-variant`, `outline`, `outline-variant` | текст, подписи, разделители |
| **night** | `night`, `night-soft` | только затемнение под фотографией и стеклянные поверхности поверх неё |
| **error** | `error`, `error-container`, `on-error-container` | ошибки и только они |

Красный — редкий и дорогой. Если на экране два-три красных пятна, лишние
перекрашиваются в `surface-container-high` (нейтральная кнопка) или
`secondary`/`tertiary` по смыслу.

## 2. Светлый экран и тёмное стекло

Приложение светлое: пергамент, тёплые тени, тёмные чернила. **Тёмное стекло
берём только там, где под ним фотография, карта или видео** — иначе тёмная
плашка на пергаменте выглядит дырой.

- Светлая карточка:
  `rounded-2xl bg-surface-container-lowest p-space-md shadow-document`
- Тёмная стеклянная (поверх фото/карты):
  `rounded-2xl border border-white/15 bg-night/45 p-space-md shadow-sheet backdrop-blur-md`
- Затемнение под стеклом: слой `bg-night/45` плюс
  `bg-gradient-to-b from-night/20 via-transparent to-night/70` — гуще снизу, под
  мелким текстом.

Разрешённые места для тёмного стекла: экран входа, «геройская» шапка экрана с
фотографией, AR, экран `excursion-walk`, плеер живого портрета, панели поверх
карты. Везде ещё — светлая карточка.

## 3. Типографика

Один шрифт — Manrope, размеры только токенами, всегда парой `font-*` + `text-*`:

- `font-headline-xl text-headline-xl` — титул экрана входа. Больше нигде.
- `font-headline-lg text-headline-lg` — заголовок раздела (шапка экрана).
- `font-headline-md text-headline-md` — заголовок блока внутри экрана.
- `font-headline-sm text-headline-sm` — заголовок карточки.
- `font-body-md text-body-md` — основной текст, `font-body-sm text-body-sm` — пояснения.
- `font-label-lg/md/sm` — кнопки, поля, подписи; `label-sm` ещё и для мелких метрик.
- `font-archival text-archival uppercase` — надзаголовок-рубрика («АРХИВ»,
  «ИЛИ ВОЙТИ ЧЕРЕЗ»). На светлом — `text-on-surface-variant`, на стекле — `text-white/70`.

Блик `ribbon-shimmer` — редкая роскошь: **один раз на экран**, на самом
заголовке. На светлом фоне обязательно задать базовый цвет:
`class="ribbon-shimmer [--shimmer-base:theme(colors.ink.DEFAULT)]"` — иначе буквы
станут белыми. Разводить соседние блики `[animation-delay:700ms]`.

## 4. Ритм и отступы

- Боковые поля экрана — только `px-margin`. Никаких `px-4`.
- Вертикальный ритм: `gap-space-sm` внутри блока, `gap-space-md` между блоками,
  `space-lg/xl` — крупные паузы. Внутренний отступ карточки — `p-space-md`.
- Низкий экран (iPhone SE и подобные) — вариант `short:`: на нём ужимаются
  отступы и кегль, экран должен помещаться целиком. Проверять на 375×667.
- Шапка и нижняя панель висят поверх контента: экраны с вкладками отступают
  `pt-header` / `pb-nav`, это уже делает лэйаут — руками не дублировать.

## 5. Рецепты

**Главная кнопка экрана** (одна на экран):

```html
<button class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5">
```

Помни: `rounded-xl` в этой шкале — 3rem, то есть таблетка. Для карточек —
`rounded-2xl` (1rem), для мелких плашек — `rounded-DEFAULT`/`rounded-lg`.

**Вторичная кнопка:**
`rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95`

**Поле ввода** — строка, а не коробка: иконка слева, линия снизу, в фокусе
светлеет. На светлом: `border-b border-outline-variant focus-within:border-primary`,
иконка `text-on-surface-variant`. На стекле — см. `auth/components/AuthField.vue`.
Общие поля живут в `src/ui/form/`.

**Переключатель двух режимов** — подложка едет трансформацией, а не
перекрашиваются кнопки (`AuthPage.vue`, блок `role="tablist"`). Тот же приём
годится для любых двух-трёх режимов экрана.

**Плашка ошибки:** `rounded-xl bg-error/90 px-space-sm py-2 text-center font-body-sm text-body-sm text-white`
на стекле, `bg-error-container text-on-error-container` — на светлом. Ошибка
**занимает место подсказки**, а не встаёт сверху неё.

**Формы** — `ui/form/FormInput`, `FormSelect`, `FormTextarea`. Классы графы
вынесены в `ui/form/styles.ts` (`FIELD_LABEL_CLASS`, `FIELD_LINE_CLASS`,
`INPUT_CLASS`, `TEXTAREA_CLASS`, `FIELD_HINT_CLASS`) — своё поле собирайте из
них, а не заново. У `FormInput` и `FormSelect` есть необязательная иконка
(`icon`) и слот `trailing` под кнопку или единицу измерения.

**Карта** — `ui/geo/GeoMap`. Предметной области она не знает: метки, линии,
радиусы (`circles`, тип `ui/geo/circles.ts`) и подпись приходят пропсами, цвет
метки — `tone` из палитры. Своей карты не заводим.

**Иконки** — только `MsIcon` с размером пропсом: 15 (в кружке), 18 (в строке),
20–24 (в шапке), 28 (в пустом состоянии). `filled` — для «наградных» и активных.

## 6. Движение

- Всё, что меняет высоту рядом с видимым контентом, **раскрывается, а не
  появляется**: обёртка `grid` + `grid-rows-[0fr] → grid-rows-[1fr]`,
  внутренний `div` с `overflow-hidden`, `transition-[grid-template-rows,opacity]
  duration-300 ease-out`, скрытая графа помечена `inert`. `v-if` для таких
  блоков — источник скачков, так делать нельзя.
- Длительности: 200 мс — цвет и мелочь, 300 мс — высота и переезд, 500+ —
  только полноэкранное.
- Нажатие: `active:scale-[0.99]` у крупных кнопок, `active:scale-95` у мелких.
- Уважаем `prefers-reduced-motion` — декоративное движение в нём выключается
  (см. `ribbon-shimmer` в `style.css`).

## 7. Состояния экрана

Не изобретаем свои — берём готовые из `src/ui/`:

- `StateBlock` — загрузка / ошибка с «Повторить» / пусто. Каждый экран, который
  ходит в сервис, обязан показывать все три.
- `InlineNotice` — короткое сообщение по месту (`info` / `success` / `error`).
- `AccountRequired` — действие требует входа; демо-режиму показываем это, а не
  молча выключенную кнопку.
- `DemoDataBadge` — данные демонстрационные, а не с сервиса. Показывать честно.
- `SheetDialog` — всё, что «выезжает снизу»: формы, подтверждения, фильтры.

## 8. Доступность

- Кнопка — `<button type="button">`, ссылка — `RouterLink`. Не наоборот.
- У иконочной кнопки обязателен `aria-label`; у переключателя — `role="switch"`
  и `aria-checked`; у вкладок — `role="tab"` и `aria-selected`.
- Скрытое схлопнутое — `inert`. Живые сообщения — `role="alert"` / `role="status"`.
- Фокус виден: глобальный `:focus-visible` уже задан, не отключать.
- Кегль меньше `label-sm` не используем.

## 9. Чего не делаем

- Произвольные цвета, шрифты, тени, радиусы мимо токенов.
- Кнопки-обманки: либо кнопка работает, либо её нет. Единственное исключение —
  кнопки внешних сервисов на экране входа (провайдеры ещё не подключены).
- Пометки «тест», «demo», «coming soon» на живых экранах. Нечестное состояние
  показываем текстом в `InlineNotice`, а не значком на кнопке.
- Английские подписи в интерфейсе. Кавычки — «ёлочки», тире — длинное.
- Комментарии, пересказывающие код. Комментарий объясняет **почему** так, и
  только там, где решение неочевидно, — как в существующих файлах.
