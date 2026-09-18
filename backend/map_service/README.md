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

## Гео без PostGIS

Координаты хранятся как `lat`/`lon` (float). Поиск «рядом» — bbox-предфильтр
в SQL (`core/geo.bbox_around`) + точный `haversine` в Python
(`core/geo.haversine_km`). Прод-апгрейд — PostGIS: `geography(Point)`,
GiST-индекс, `ST_DWithin`.

## Эндпоинты

### Слой «ВОВ» — `/poi`
| Метод | Путь | Доступ | |
| --- | --- | --- | --- |
| GET | `/poi` | публично | фильтры: `kind`, `q`, bbox (`min_lat…max_lon`) |
| GET | `/poi/nearby` | публично | `lat`, `lon`, `radius_km`, `kind` → сортировка по расстоянию |
| POST | `/poi` | любой авторизованный | |
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
| PATCH | `/last-stand/{id}/status` | `moderator` / root | |
| DELETE | `/last-stand/{id}` | автор или `moderator`/root | |

`status`: `discovered` → `archive_confirmed` → `remains_raised`.

## Как ходит admin_service

`/internal/*` (список, статистика, смена статуса, удаление точек) принимает
`X-Actor-Id`, но ни `PointOfInterest`, ни `LastStandPoint` не хранят, кто
именно поменял статус или удалил запись через админку — атрибуции для этих
действий нет (в отличие от `created_by`, который остаётся полем автора,
создавшего запись через обычный JWT). Известное ограничение, не баг.

## Дальше

- Импорт синтетики жюри (`mock_graves.csv`, `mock_battles.json`).
- Событие «новая точка Последнего боя» → очередь для `notification_service`
  (пуш волонтёрам в радиусе).
- PostGIS + слои маршрутов из `route_service`.
