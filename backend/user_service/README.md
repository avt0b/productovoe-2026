# user_service

Профили пользователей платформы «Маршруты победы»: семьи, поисковики,
краеведы, наставники. Хранит анкетные данные и настройки гео-оповещений
«Последнего боя».

## Запуск

```bash
uv sync
cp .env.example .env      # JWT_SECRET должен совпадать с auth_service
uv run uvicorn main:app --reload --port 8002
```

Swagger — <http://127.0.0.1:8002/docs>.

## Тесты

```bash
uv run pytest        # sqlite во временном файле, Postgres не нужен
uv run ruff check .
```

## Архитектура (3 слоя)

```
api/           # HTTP-слой: роутеры (profiles.py, internal.py), pydantic-схемы, deps
services/      # ProfileService — бизнес-логика, включая ленивое создание профиля
repositories/  # ProfileRepository — доступ к БД
core/          # config, db, security (проверка JWT), exceptions, models/
main.py        # сборка FastAPI
```

## Модель

`Profile` — id совпадает с `sub` из JWT (не отдельный UUID, профиль
физически не может существовать без пользователя в `auth_service`):

- `display_name`, `city`, `bio` — по умолчанию пустые строки.
- `avatar_url` — опционально.
- `role` — кэш роли из JWT: при каждом обращении владельца (`GET`/`PUT
  /profiles/me`) молча пересинхронизируется, если роль в токене успела
  измениться в `auth_service`. Не независимый источник истины.
- `squad_id` — опционально, id отряда из `search_hq_service`; сервис его не
  валидирует.
- `is_verified` — по умолчанию `false`.
- `subscribed_to_search`, `alert_radius_km` (по умолчанию `20`, диапазон
  `1–200`) — гео-оповещения о находках рядом.

## Эндпоинты

| Метод | Путь | Доступ |
| --- | --- | --- |
| GET | `/profiles/me` | любой авторизованный — создаёт профиль лениво при первом обращении (`get_or_create_own`) |
| PUT | `/profiles/me` | любой авторизованный — обновляет только присланные поля |
| GET | `/profiles` `?role&limit&offset` | только `is_root` |
| GET | `/profiles/{id}` | любой авторизованный |
| PATCH | `/profiles/{id}/verify` | `local_historian` / `mentor` / `moderator` / root |

**`GET /profiles/{id}` не проверяет владение** — любой обладатель валидного
токена может прочитать чужой профиль целиком (`city`, `bio`,
`subscribed_to_search`, `alert_radius_km` и т.д.) по id. Это осознанное
упрощение MVP, а не баг: скрывать данные постранично здесь пока незачем.

`PATCH /profiles/{id}/verify` — доступ шире, чем можно предположить из
названия: не только `moderator`, но и `local_historian`/`mentor` тоже могут
подтверждать чужой статус (`_VERIFIER_ROLES` в `services/profile_service.py`).

## Аутентификация

Сервис **не** аутентифицирует сам — принимает `access`-JWT от `auth_service`
и проверяет подпись локально (**HS256**, общий `JWT_SECRET`, тот же `issuer`
и обязательный `typ=access`). Из токена берутся `sub` (id пользователя = id
профиля), `role`, `is_root`.

## Как ходит admin_service

`/internal/*`: `GET /internal/stats` (сводка для дашборда, включая разбивку
«кто ждёт верификации роли»), `GET /internal/profiles?query&role&is_verified`
(поиск по имени/городу), `GET /internal/profiles/{id}`, `PATCH
/internal/profiles/{id}/verify` — верификация в обход обычных ролей
(`X-Internal-Key` даёт актору `is_root=True`). `X-Actor-Id` при этом
принимается, но у `Profile` нет поля-атрибуции (`verified_by` и т.п.) — кто
именно подтвердил через админку, нигде не сохраняется. Известное
ограничение, не баг и не потерянная фича.

## Дальше

- Достижения и прогресс по маршрутам (геймификация) — сейчас только
  декоративные данные на фронте, здесь этого нет.
- Поле-атрибуция для верификации через `/internal/*`.
