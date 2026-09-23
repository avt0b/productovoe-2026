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
| GET | `/achievements/me` | любой авторизованный — свои значки (`code`, `earned_at`) |
| GET | `/notifications` `?unread_only&limit&offset` | владелец — своя лента |
| POST | `/notifications/{id}/read` | владелец |
| POST | `/notifications/devices` | любой авторизованный — регистрирует токен устройства (upsert по `token`) |
| DELETE | `/notifications/devices/{token}` | владелец токена |

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

## Достижения

`UserAchievement` (`user_id`, `code`, `earned_at`, уникален по `(user_id,
code)`) — значки за активность (геймификация из ТЗ). `code` — свободная
строка, а не Enum в БД, по тому же принципу, что `Notification.kind`: новый
повод для ачивки заводит сервис-источник события, `user_service` под это не
редеплоится. Человекочитаемые заголовки для текста уведомления — словарь
`ACHIEVEMENT_TITLES` в `core/models/achievement.py`; для неизвестного кода
просто показываем сам код.

Выдаёт `POST /internal/achievements/award` (`X-Internal-Key`, вызывается
напрямую сервисами-источниками события — по тому же принципу, что
`broadcast-nearby`, не только `admin_service`). Идемпотентно: повторный
`award` тем же `(user_id, code)` не создаёт дубликат и не шлёт уведомление
ещё раз, так что вызывающий сервис может дёргать её на каждое подходящее
действие, не проверяя заранее, было ли оно первым. Успешная выдача создаёт
обычное `Notification` (`kind="achievement"`) в уже существующей ленте.

Сейчас выдаются:

| Код | Кто выдаёт | Когда |
| --- | --- | --- |
| `first_route_completed` | route_service | маршрут пройден целиком (`completed_at` выставлен) |
| `archive_helper` | archive_service | любой `verify`/`reject` записи архива |
| `trip_volunteer` | search_hq_service | регистрация на «Выходные с поисковиком» |
| `donor` | search_hq_service | донат стал `succeeded` (сразу или после вебхука ЮKassa) |

Видны и на своём, и на чужом профиле: `ProfileOut.achievements` заполняется
и в `GET /profiles/me`, и в `GET /profiles/{id}` — тем же «не проверяет
владение», что и остальные поля профиля (см. выше).

## Push-доставка

`Notification` создаётся в двух местах (`broadcast_nearby` для «Последнего
боя», `AchievementService.award` для значков) — оба после коммита зовут
`services/push_service.py`, который шлёт push на все устройства владельца
через `services/fcm_client.py` (FCM HTTP v1). Один API покрывает Android,
iOS (FCM сам разносит на APNs) и веб (Web Push) — платформа в
`NotificationDevice.platform` на формат запроса не влияет.

Не настроено (`FCM_PROJECT_ID`/ключ сервисного аккаунта не заданы) —
`push_service.deliver` выходит первой же проверкой, ничего не пытаясь
сделать: push — не блокирующая зависимость, лента и ачивки работают как
раньше. Настроено, но FCM ответил `UNREGISTERED`/`404` на конкретный токен —
устройство удаляется из `NotificationDevice` (протухший токен, не временная
ошибка). Любая другая ошибка/недоступность FCM — просто `warning` в лог,
доставка этого уведомления не повторяется (retry-очереди нет, как и у
остальных внутрисервисных вызовов в проекте).

Отдельно нет своего микросервиса `notification_service` из `backend/README.md`
— решили не заводить: токены устройств и так уже в этой БД
(`NotificationDevice`), а доставка не хранит собственное состояние между
запросами (кроме кэша OAuth2-токена в памяти процесса), так что отдельная
БД/деплой ради неё не нужны.

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

- Поле-атрибуция для верификации через `/internal/*`.
