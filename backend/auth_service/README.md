# auth_service

Сервис аутентификации платформы «Маршруты победы». Вход по **email + паролю**,
выдача и ротация JWT.

## Запуск

```bash
uv sync
cp .env.example .env          # при необходимости поправьте JWT_SECRET / DATABASE_URL
uv run uvicorn main:app --reload --port 8001
```

Swagger — <http://127.0.0.1:8001/docs>.

По умолчанию `DATABASE_URL` указывает на PostgreSQL. Для быстрого локального
прогона можно временно поставить `DATABASE_URL=sqlite+pysqlite:///./auth.sqlite`.
Схема создаётся на старте (`init_db`), миграции alembic — задел на потом.

## Тесты

```bash
uv run pytest          # sqlite во временном файле, Postgres не нужен
uv run ruff check .
```

## Архитектура (3 слоя)

```
api/           # HTTP-слой: роутеры + pydantic-схемы валидации + deps
  routers/     #   auth.py (register/login/refresh/logout/me), admin.py (is_root)
  schemas/     #   auth.py, user.py
  deps.py      #   get_db, фабрики сервисов, get_current_user, require_root
services/      # бизнес-логика: AuthService, UserAdminService, bootstrap
repositories/  # доступ к БД: UserRepository, RefreshTokenRepository
core/          # config, db (инициализация), security, exceptions, models/
main.py        # сборка FastAPI, обработчик доменных ошибок, lifespan
```

Правило слоёв: роутер парсит запрос и вызывает сервис; сервис оркеструет
репозитории и владеет транзакцией (`commit`); репозиторий делает только SQL.
Доменные ошибки (`core/exceptions.py`) сервис бросает как есть — `main.py`
превращает их в HTTP-ответ.

## Модель авторизации

- **Токен:** JWT **HS256** с общим секретом `JWT_SECRET` (тот же секрет у
  остальных сервисов — проверяют подпись локально, без вызова auth).
  Прод-апгрейд — RS256 с приватным ключом только здесь.
- **Пара токенов:** `access` (~15 мин, в нём `sub`, `role`, `is_root`) +
  `refresh` (~30 дней). В БД хранится только SHA-256 хэш refresh-токена.
  При `/auth/refresh` — ротация; повторное использование старого токена
  трактуется как компрометация и отзывает всю цепочку сессий пользователя.
- **Пароли:** Argon2id (`argon2-cffi`), прозрачный re-hash при смене параметров.
- **`role`** — Enum (`family` / `searcher` / `local_historian` / `mentor` /
  `moderator`), задаётся при регистрации, меняется только из админки.
- **`is_root`** — отдельный булев флаг доступа в админку, не роль. Первый
  администратор создаётся на старте из `BOOTSTRAP_ROOT_EMAIL` / `_PASSWORD`.

## Эндпоинты

| Метод и путь                      | Доступ            | Назначение                          |
| --------------------------------- | ----------------- | ----------------------------------- |
| `POST /auth/register`             | публично          | регистрация (email, пароль, роль)   |
| `POST /auth/login`                | публично          | выдача пары токенов                 |
| `POST /auth/refresh`              | refresh-токен     | ротация пары токенов                |
| `POST /auth/logout`               | refresh-токен     | отзыв refresh-токена                |
| `GET  /auth/me`                   | access-токен      | текущий пользователь                |
| `POST /auth/change-password`      | access-токен      | смена пароля + разлогин всех сессий |
| `GET  /admin/users`               | `is_root`         | список пользователей                |
| `PATCH /admin/users/{id}/role`    | `is_root`         | сменить роль                        |
| `PATCH /admin/users/{id}/active`  | `is_root`         | включить/отключить учётку           |
| `PATCH /admin/users/{id}/root`    | `is_root`         | выдать/снять доступ в админку       |

## Дальше

- OTP по телефону, OAuth (VK ID / Yandex ID / Госуслуги), гостевой режим.
- alembic-миграции вместо `create_all`.
