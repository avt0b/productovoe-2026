# archive_service

«Народный архив» / «Живая память» (модуль 6 ТЗ): пользователи предлагают
события, карточки бойцов и воспоминания, а краевед / наставник / модератор
их подтверждает.

## Запуск

```bash
uv sync
cp .env.example .env          # JWT_SECRET = как в auth_service; DATABASE_URL -> БД archive
uv run uvicorn main:app --reload --port 8005
```

Swagger — <http://127.0.0.1:8005/docs>. Тесты: `uv run pytest`.

## Модель

`ArchiveEntry`:
- `kind`: `event` / `soldier_card` / `memory` / `photo_story`
- `title`, `body`, опциональные `lat`/`lon` (привязка к точке маршрута),
  `event_date` / `date_text`, `media_url`
- `submitted_by` (из JWT)
- `status`: `pending` → `verified` / `rejected`
- `verified_by`, `reviewed_at`, `review_note`

## Логика доступа

| Действие | Кто |
| --- | --- |
| `GET /entries` | публично — **только `verified`** |
| `GET /entries/{id}` | `verified` — все; `pending`/`rejected` — автор или верификатор |
| `GET /entries/mine` | автор (все свои, любой статус) |
| `GET /entries/moderation?status=` | `local_historian` / `mentor` / `moderator` / root |
| `POST /entries` | любой авторизованный → `pending` |
| `PATCH /entries/{id}` | автор (пока `pending`) или верификатор |
| `POST /entries/{id}/verify` · `/reject` | `local_historian` / `mentor` / `moderator` / root |
| `DELETE /entries/{id}` | верификатор, либо автор пока `pending` |

## Дальше

- Механика «помочь проверить» на маршруте: если рядом с точкой есть
  неподтверждённая запись — предложить пользователю (геймификация).
- Связь `soldier_card` с `media_service` («Живое фото»).
- Полнотекстовый поиск (сейчас `ILIKE`).
