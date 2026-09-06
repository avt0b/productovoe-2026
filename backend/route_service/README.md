# route_service

Семейный навигатор платформы «Маршруты победы» (модуль 2 ТЗ): квест-маршруты
для детей и родителей — точки с историей, заданиями, аудиоспектаклями и
AR-подсказками, плюс отслеживание прогресса.

## Запуск

```bash
uv sync
cp .env.example .env          # JWT_SECRET = как в auth_service; DATABASE_URL -> БД routes
uv run uvicorn main:app --reload --port 8006
```

Swagger — <http://127.0.0.1:8006/docs>. Тесты: `uv run pytest`.

## Сущности

- **Route** — маршрут: `mode` (`family` / `general`), `city`, `distance_km`,
  `is_published` (черновик виден только автору и модератору).
- **Waypoint** — точка: `order_index`, координаты, `poi_id` (ссылка на точку
  слоя «ВОВ» в `map_service`), `story`, `kid_task` («Найди калибр пушки»),
  `audio_url`, `ar_hint`.
- **RouteProgress** — прогресс семьи: `completed_waypoint_ids` (в порядке
  маршрута), `current_index`, `completed_at`; уникален по `(route_id, user_id)`.

## Эндпоинты

| Метод | Путь | Доступ |
| --- | --- | --- |
| GET | `/routes` `?mode&city` | публично — только опубликованные |
| GET | `/routes/mine` | автор (свои, включая черновики) |
| POST | `/routes` | `local_historian` / `mentor` / `moderator` / root |
| GET | `/routes/{id}` | опубликованный — все; черновик — автор / модератор |
| PATCH · DELETE | `/routes/{id}` | автор / модератор / root |
| POST | `/routes/{id}/publish` | автор / модератор (нужна ≥1 точка) |
| GET | `/routes/{id}/waypoints` | как у маршрута |
| POST | `/routes/{id}/waypoints` | автор / модератор |
| PATCH · DELETE | `/waypoints/{id}` | автор / модератор |
| POST | `/routes/{id}/waypoints/reorder` | автор / модератор |
| POST | `/routes/{id}/progress/start` | любой авторизованный (идемпотентно) |
| POST | `/routes/{id}/progress/complete-waypoint` | любой авторизованный |
| GET | `/routes/{id}/progress/me` | любой авторизованный |

## Дальше

- Автогенерация маршрута: подтянуть точки из `map_service` (`/poi/nearby`)
  по городу/радиусу и собрать черновик — «Автоматически строить квест-маршруты».
- Аудиоспектакли и AR-контент через `media_service`.
- Ачивки за пройденные маршруты → `user_service` (геймификация).
