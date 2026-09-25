# map_service

Картографический сервис платформы «Маршруты победы»: слой **«ВОВ»** (захоронения,
места боёв, памятники, госпитали, окопы, аэродромы) и карта **«Последний бой»**
(места гибели красноармейцев — модуль 8 ТЗ).

## Запуск

```bash
uv sync
cp .env.example .env          # JWT_SECRET = как в auth_service; DATABASE_URL -> БД map
uv run uvicorn main:app --reload --port 8003
```

Swagger — <http://127.0.0.1:8003/docs>. Тесты: `uv run pytest`, линт: `uv run ruff check .`.

Чтобы до сервиса достучался телефон с APK — `--host 0.0.0.0` и адрес компьютера
в локальной сети в `.env` клиента.

## Демо-точки Орловской области

```bash
uv run python -m scripts.seed_orel
```

Заливает слой «ВОВ» (13 мест) и «Последний бой» (5 точек, все три статуса).
Повторный запуск ничего не дублирует: id постоянные. Схему скрипт создаёт сам.

- **Слой «ВОВ» — реальные места.** Мемориалы Орла — с координатами из
  OpenStreetMap. У сёл и городов области — координаты населённого пункта, а
  точное место памятника надо уточнить у краеведов: это записано в `source`.
- **«Последний бой» — демо по сценариям кейса** («Иванов И. И., овраг у
  Крупышино», три десантника 9-й бригады). `source` начинается с «ДЕМО», чтобы
  такие точки не приняли за Книгу Памяти. Удалить демо —
  `created_by = 'seed-orel'`.

## CORS

Клиентское приложение ходит в сервис напрямую, поэтому его origin должен быть в
`CORS_ORIGINS`. По умолчанию разрешены dev-сервер клиента (`:5174`) и APK
(`https://localhost` — так Capacitor на Android отдаёт приложение).

## Архитектура

Стандартный трёхслойный скелет (`api` / `services` / `repositories` + `core`),
см. [../README.md](../README.md).

## Гео: PostGIS с фолбэком на Python

Координаты хранятся как `lat`/`lon` (float) — это источник истины и то, что
отдаётся наружу. На Postgres `init_db()` (`core/db._ensure_postgis`) сам,
идемпотентно, доустанавливает: `CREATE EXTENSION postgis`, сгенерированную
колонку `geog geography(Point,4326)` (STORED, пересчитывается из lat/lon без
отдельной записи) и GiST-индекс на ней. `POIService.nearby` /
`LastStandService.nearby` проверяют диалект БД (`core.db.engine.dialect.name`)
и идут в `*_repository.nearby_postgis` — `ST_DWithin` + сортировка по `<->`
(KNN, использует индекс), реальный индексированный радиус-поиск.

На sqlite (весь тестовый набор — PostGIS с ним несовместим) и на любой другой
БД без PostGIS автоматически остаётся прежний фолбэк: bbox-предфильтр в SQL
(`core/geo.bbox_around`) + точный `haversine` в Python
(`core/geo.haversine_km`). Ответ API идентичен в обоих режимах — clients об
этом не знают.

## Эндпоинты

### Слой «ВОВ» — `/poi`
| Метод | Путь | Доступ | |
| --- | --- | --- | --- |
| GET | `/poi` | публично | фильтры: `kind`, `q`, bbox (`min_lat…max_lon`) |
| GET | `/poi/nearby` | публично | `lat`, `lon`, `radius_km`, `kind` → сортировка по расстоянию |
| POST | `/poi` | `searcher` / `local_historian` / `mentor` / `moderator` / root | |
| GET | `/poi/{id}` | публично | |
| PATCH | `/poi/{id}` | автор или `moderator`/root | |
| DELETE | `/poi/{id}` | автор или `moderator`/root | |

`kind`: `grave` `battle` `monument` `hospital` `trench` `airfield` `other`.

### Карта «Последний бой» — `/last-stand`
| Метод | Путь | Доступ | |
| --- | --- | --- | --- |
| GET | `/last-stand` | публично | фильтры: `status`, `q`, bbox |
| GET | `/last-stand/nearby` | публично | для пуш-оповещений волонтёрам (радиус из профиля) |
| POST | `/last-stand` | `searcher` / `local_historian` / `mentor` / `moderator` / root | |
| GET | `/last-stand/{id}` | публично | |
| PATCH | `/last-stand/{id}` | автор или `moderator`/root | |
| PATCH | `/last-stand/{id}/status` | `moderator` / root | тело: `status` + необязательное `note` — на основании чего |
| GET | `/last-stand/{id}/history` | публично | кто и почему менял стадию, от первой записи к последней |
| DELETE | `/last-stand/{id}` | автор или `moderator`/root | |

`status`: `discovered` → `archive_confirmed` → `remains_raised`.

Каждая смена стадии пишется в `last_stand_status_changes`: кто (`actor_id`), с
какой на какую, когда и на основании чего (`note` — том Книги Памяти, номер
дела). Записи только добавляются: строку истории нельзя ни поправить, ни
удалить, иначе она ничего не стоит. Повторная установка той же стадии строки
не добавляет.

## Как ходит admin_service

`/internal/*` (список, статистика, смена статуса, удаление точек) принимает
`X-Actor-Id`. Смена стадии «Последнего боя» этот id сохраняет — в истории
(`last_stand_status_changes.actor_id`) вместе с основанием, которое админ
написал в admin_service. У остальных действий (правка и удаление точек, слой
«ВОВ») атрибуции по-прежнему нет — только `created_by` автора записи.
Известное ограничение, не баг.

## Уведомления волонтёров

При `POST /last-stand` сервис синхронно (best-effort, не роняя создание точки
при сбое) дёргает `user_service` (`services/notify_client.py`) — тот находит
подписчиков «Последнего боя» в их собственном `alert_radius_km` от домашних
координат и кладёт им уведомление в ленту. Подробности — README `user_service`.

Тем же best-effort образом (`services/stats_client.py`) шлёт туда `finds_count`
— новая точка засчитывается в статистику профиля автора (`created_by`). См.
[user_service/README.md](../user_service/README.md#статистика-профиля).

## Дальше

- Импорт синтетики жюри (`mock_graves.csv`, `mock_battles.json`).
- Слои маршрутов из `route_service` поверх карты «ВОВ» (визуальная интеграция,
  не бэкенд — API для этого уже есть с обеих сторон).
