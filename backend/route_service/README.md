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

## Демо-маршрут

```bash
uv run python -m scripts.seed_orel
```

«Тропа памяти: центр Орла» — сценарий кейса «мама с ребёнком 10 лет»:
опубликованный семейный маршрут из четырёх точек у реальных мемориалов
(координаты из OpenStreetMap) с историями, заданиями для ребёнка и
AR-подсказками. `poi_id` точек совпадает с id тех же мест, которые заливает
`map_service/scripts/seed_orel.py`: общий неймспейс uuid5, запросов между
сервисами не нужно.

## CORS

Клиентское приложение ходит в сервис напрямую — его origin должен быть в
`CORS_ORIGINS`. По умолчанию разрешены dev-сервер клиента (`:5174`) и APK
(`https://localhost`, Capacitor на Android).

## Сущности

- **Route** — маршрут: `mode` (`family` / `general`), `city`, `distance_km`,
  `is_published` (черновик виден только автору и модератору).
- **Waypoint** — точка: `order_index`, координаты, `poi_id` (ссылка на точку
  слоя «ВОВ» в `map_service`), `story`, `kid_task` («Найди калибр пушки»),
  `audio_url`, `ar_hint`, `expected_answer` (эталонный ответ на `kid_task` —
  в API наружу не отдаётся, только флаг `has_answer`).
- **RouteProgress** — прогресс семьи: `completed_waypoint_ids` (в порядке
  маршрута), `current_index`, `answers` (waypoint_id → верно ли ответили),
  `completed_at`; уникален по `(route_id, user_id)`.

## Эндпоинты

| Метод | Путь | Доступ |
| --- | --- | --- |
| GET | `/routes` `?mode&city` | публично — только опубликованные |
| GET | `/routes/mine` | автор (свои, включая черновики) |
| POST | `/routes` | `local_historian` / `mentor` / `moderator` / root |
| POST | `/routes/auto-generate` | `local_historian` / `mentor` / `moderator` / root — черновик из точек `map_service` рядом с `lat`/`lon` (`409`, если точек рядом нет) |
| GET | `/routes/{id}` | опубликованный — все; черновик — автор / модератор |
| PATCH · DELETE | `/routes/{id}` | автор / модератор / root |
| POST | `/routes/{id}/publish` | автор / модератор (нужна ≥1 точка, иначе `409`) |
| GET | `/routes/{id}/waypoints` | как у маршрута |
| POST | `/routes/{id}/waypoints` | автор / модератор |
| PATCH · DELETE | `/waypoints/{id}` | автор / модератор |
| POST | `/routes/{id}/waypoints/reorder` | автор / модератор — список id должен без пропусков и дублей совпадать с точками маршрута, иначе `404` |
| POST | `/routes/{id}/progress/start` | любой авторизованный (идемпотентно) |
| POST | `/routes/{id}/progress/complete-waypoint` | любой авторизованный — опциональный `answer` сверяется с `expected_answer` точки (не блокирует прохождение, просто не засчитывается) |
| GET | `/routes/{id}/progress/me` | любой авторизованный |
| GET | `/routes/{id}/archive-prompts` | как у маршрута — неподтверждённые заметки `archive_service` рядом с точками, «помоги проверить» (модуль 6 ТЗ) |
| GET | `/routes/{id}/media-prompts` | как у маршрута — точки без «живого фото» в `media_service`, «оживить фото бойца» (модуль 7 ТЗ) |

Завершение маршрута (`completed_at` выставляется на последней `complete-waypoint`)
шлёт `user_service` `POST /internal/achievements/award` с кодом
`first_route_completed` (`services/achievement_client.py`) — см.
[user_service/README.md](../user_service/README.md#достижения), и туда же
`POST /internal/stats/increment` с `routes_completed`
(`services/stats_client.py`) — см. [user_service/README.md](../user_service/README.md#статистика-профиля).
Недоступность user_service не мешает пройти маршрут — ни ачивка, ни счётчик
просто не обновятся.

### Автогенерация маршрута

`POST /routes/auto-generate` (модуль 2 ТЗ, «автоматически строить квест-маршруты»):
по `lat`/`lon`/`radius_km` тянет точки слоя «ВОВ» из `map_service`
(`GET /poi/nearby`, см. `services/map_client.py`), жадно строит из них
маршрут-прогулку (каждый раз ближайшая ещё не взятая точка — не «звезда» из
одного центра, как у сырого `nearby`) и создаёт черновик (`is_published=false`)
с посчитанным `distance_km`. У точек заполнены только `title`/координаты/
`poi_id`/`story` (из описания POI) — `kid_task`/`audio_url`/`ar_hint` пустые,
это уже ручная работа автора после автогенерации. `map_service` недоступен или
точек рядом нет — `409`.

## Дальше

- Аудиоспектакли и AR-контент через `media_service`.
- Ачивки за пройденные маршруты → `user_service` (геймификация).
