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

## Дальше

- Импорт синтетики жюри (`mock_graves.csv`, `mock_battles.json`).
- Событие «новая точка Последнего боя» → очередь для `notification_service`
  (пуш волонтёрам в радиусе).
- PostGIS + слои маршрутов из `route_service`.
