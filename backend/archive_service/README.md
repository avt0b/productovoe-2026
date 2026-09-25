# archive_service

«Народный архив» / «Живая память» (модуль 6 ТЗ): пользователи предлагают
события, карточки бойцов и воспоминания, а поисковик / краевед / наставник /
модератор их подтверждает.

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
  `event_date` / `date_text`
- `media_url` — фото (имя историческое), `audio_url` — аудиовоспоминание.
  Оба необязательные и могут быть у записи одновременно. Сами файлы
  загружаются через `POST /uploads` в media_service (фото до 15 МБ, аудио до
  30 МБ), сюда приходят готовые ссылки
- `submitted_by` (из JWT)
- `status`: `pending` → `verified` / `rejected`
- `verified_by`, `reviewed_at`, `review_note`

Колонку `audio_url` в уже существующей таблице досоздаёт `init_db` на старте
(`core/db.py`, `_ADDED_COLUMNS`): `create_all` существующие таблицы не меняет.
Отдельной миграции руками не нужно.

## Логика доступа

| Действие | Кто |
| --- | --- |
| `GET /entries` | публично — **только `verified`** |
| `GET /entries/{id}` | `verified` — все; `pending`/`rejected` — автор или верификатор |
| `GET /entries/mine` | автор (все свои, любой статус) |
| `GET /entries/moderation?status=` | `searcher` / `local_historian` / `mentor` / `moderator` / root |
| `POST /entries` | любой авторизованный → `pending` |
| `PATCH /entries/{id}` | автор (пока `pending`) или верификатор |
| `POST /entries/{id}/verify` · `/reject` | `searcher` / `local_historian` / `mentor` / `moderator` / root |
| `DELETE /entries/{id}` | верификатор, либо автор пока `pending` |

Каждый `verify`/`reject` шлёт `user_service` `POST /internal/achievements/award`
с кодом `archive_helper` (`services/achievement_client.py`) — геймификация
«помочь проверить» из ТЗ, достаётся верификатору. Недоступность user_service
не мешает верифицировать запись — ачивка просто не выдастся.

Отдельно, только на `verify` (не на `reject`), туда же летит
`POST /internal/stats/increment` с `finds_count` — но уже **автору записи**
(`submitted_by`), не верификатору: это статистика профиля «сколько находок»,
не ачивка. См. [user_service/README.md](../user_service/README.md#статистика-профиля).

### Служебная заметка (`review_note`) не публична

`review_note` — комментарий верификатора (обычно виден только на `reject`, но
техничеcки может быть заполнен и на `verify`). Он присутствует в ответе
только автору записи и верификаторам (`searcher`/`local_historian`/`mentor`/
`moderator`/root); для всех остальных — как для анонима в `GET /entries`, так
и для постороннего в `GET /entries/{id}` — поле отсутствует в ответе
(`EntryPublicOut` вместо `EntryOut`). `verified_by`/`reviewed_at` при этом
остаются публичными как и раньше.

### След правки и удаления уже проверенной записи

У `ArchiveEntry` нет отдельного поля audit-лога, поэтому эти два случая
покрыты так:

- **Правка верификатором уже проверенной (`verified`/`rejected`) записи** —
  `verified_by`/`reviewed_at` переносятся на того, кто редактировал, и на
  момент правки (исходный `review_note` при этом не трогается — правка
  контента не тождественна повторному verify/reject).
- **Удаление уже проверенной записи** — необратимо (строка пропадает из БД
  целиком), поэтому фиксируется только структурным логом (`logging`,
  `services/entry_service.py`), не в самой БД.

## Дальше

- Механика «помочь проверить» на маршруте: если рядом с точкой есть
  неподтверждённая запись — предложить пользователю (геймификация).
- Связь `soldier_card` с `media_service` («Живое фото»).
- Полнотекстовый поиск (сейчас `ILIKE`).
