# search_hq_service

«Поисковый штаб» платформы «Маршруты победы»: отряды, карта их потребностей,
целевые сборы (краудфандинг) и календарь выездов **«Выходные с поисковиком»**
(модули 3–4 ТЗ).

## Запуск

```bash
uv sync
cp .env.example .env          # JWT_SECRET = как в auth_service; DATABASE_URL -> БД search_hq
uv run uvicorn main:app --reload --port 8004
```

Swagger — <http://127.0.0.1:8004/docs>. Тесты: `uv run pytest`.

## Архитектура

Стандартный трёхслойный скелет (`api` / `services` / `repositories` + `core`).
Проверки прав вынесены в `services/permissions.py`.

## Сущности

- **Squad** — поисковый отряд (командир = `leader_id` из JWT).
- **SquadNeed** — потребность: `volunteers` / `funds` / `equipment`,
  `target_amount` + `collected_amount`, статус `open` / `closed`.
- **Donation** — взнос в денежный сбор; при достижении цели сбор
  автоматически закрывается.
- **VolunteerTrip** — выезд с датой, `capacity` и чек-листом новичка.
- **TripRegistration** — запись волонтёра (`registered` / `cancelled`),
  уникальна по `(trip_id, user_id)`, проверяется вместимость.

## Эндпоинты

| Метод | Путь | Доступ |
| --- | --- | --- |
| POST | `/squads` | `searcher` / `moderator` / root |
| GET | `/squads` `?region&q` | публично |
| GET/PATCH/DELETE | `/squads/{id}` | чтение — все; изменение — командир / `moderator` / root |
| GET | `/squads/{id}/needs` `?kind&status` | публично |
| POST | `/squads/{id}/needs` | командир отряда / `moderator` / root |
| GET | `/needs` `?kind&status` (по умолчанию `open`) | публично |
| PATCH | `/needs/{id}` · POST `/needs/{id}/close` | командир / `moderator` / root |
| POST | `/needs/{id}/donations` | любой авторизованный (сбор `funds`, статус `open`) |
| GET | `/needs/{id}/donations` | публично |
| GET | `/trips` `?upcoming_only` | публично |
| POST | `/squads/{id}/trips` · PATCH `/trips/{id}` | командир / `moderator` / root |
| POST | `/trips/{id}/registrations` | любой авторизованный (учёт мест) |
| DELETE | `/trips/{id}/registrations/me` | сам волонтёр |
| GET | `/trips/{id}/registrations` | командир / `moderator` / root |

## Дальше

- Модуль коллективных заявок школ/клубов на экскурсии (модуль 5 ТЗ) —
  `ExcursionRequest` + рейтинг гидов.
- Интеграция платежей (ЮKassa / CloudPayments) вместо «виртуальных» донатов.
- Событие «новый выезд» / «сбор закрыт» → `notification_service`.
