# Бэкенд: «Я потерялся» и рейтинг краеведов

Ты делаешь **только бэкенд** двух фич проекта «Маршруты победы»:
`backend/search_hq_service` и небольшие правки в `backend/user_service`.
Мобильное приложение параллельно пишет другой человек со своим Claude по
[MOBILE.md](./MOBILE.md). Вы встречаетесь только в [CONTRACT.md](./CONTRACT.md).

## Первым делом прочитай

1. [CONTRACT.md](./CONTRACT.md) — целиком. Это закон: пути, поля, коды,
   тексты ошибок и уведомлений должны совпасть **буква в букву**. Мобилка
   показывает `detail` как есть и рисует экраны по примерам JSON оттуда.
   Считаешь, что в контракте ошибка, — не отступай молча: напиши об этом в
   отчёте и предложи правку контракта.
2. `backend/search_hq_service/README.md` и код, на который ты опираешься:
   - `services/walk_service.py` — прогулка: позиции группы, выход, завершение, срок;
   - `services/excursion_service.py` — экскурсии, `_credit_excursion_completion`
     (единая точка «экскурсия завершилась»), `_close_if_expired`, `cancel`;
   - `services/rating_service.py`, `repositories/rating_repository.py`,
     `api/routers/guides.py`, `api/schemas/rating.py` — оценки, которые уже есть;
   - `services/notify_client.py`, `services/achievement_client.py` — как
     `search_hq` ходит в `user_service` (синхронно, `httpx`, ошибки глотаются
     с `logger.warning`);
   - `core/db.py` — схема создаётся через `create_all` на старте. Новые
     **таблицы** появятся сами. Новые **колонки** в старых таблицах —
     только через `_ADDED_COLUMNS` (в этой задаче новых колонок в старых
     таблицах нет);
   - `tests/conftest.py`, `tests/test_walk.py`, `tests/test_ratings.py` — как
     устроены тесты (SQLite, `TestClient`, `auth_header`, фикстура `sent`
     подменяет `notify_client.notify_users`).
3. `backend/user_service/api/routers/internal.py`,
   `repositories/family_link_repository.py`, `api/schemas/profile.py`.

## Ветки и порядок

- `feat/lost-alert-api` от `origin/develop`: разделы 1, 2 и 3 ниже.
- `feat/guide-rating-api` **от `feat/lost-alert-api`** (базой PR —
  `feat/lost-alert-api`): раздел 4. Он пользуется `profile_client`, который
  появляется в первой ветке.
- Коммиты с префиксами `feat(search_hq): …`, `feat(user_service): …`,
  `test(search_hq): …`. Комментарии в коде — по-русски, объясняют «почему», а
  не пересказывают код. Смотри, как это сделано в `walk_service.py`.
- PR в GitHub с описанием, что сделано и как проверено. Мержит человек.

---

## 1. `user_service`

### 1.1. `GET /internal/family/{user_id}`

В `api/routers/internal.py` (у роутера уже висит `require_internal_key`):

```python
@router.get("/family/{user_id}", response_model=FamilyIdsOut, summary="Семья человека — для search_hq")
def family_of(user_id: str, db: DbSession) -> FamilyIdsOut:
    ...
```

- Схема `FamilyIdsOut(BaseModel)`: `user_id: str`, `member_ids: list[str]`
  (положи в `api/schemas/family_link.py`).
- Связи в `family_links` лежат парами в обе стороны (см.
  `FamilyLinkService.redeem_invite`), поэтому хватает
  `FamilyLinkRepository(db).for_owner(user_id)` → `member_id`. Убери дубли,
  сохрани порядок.
- Нет семьи — `{"user_id": "...", "member_ids": []}`, не `404`.

Тесты в `tests/test_internal.py`: без ключа — `403`; семья из двух человек
(сделай приглашение и погаси его через публичные ручки `/family-links/invite`
и `/family-links/redeem`) видна с обеих сторон; у одинокого — пустой список.

### 1.2. `city` в `ProfileBriefOut`

В `api/schemas/profile.py` добавь `city: str` в `ProfileBriefOut` (поле у
модели `Profile` есть). Проверь, что `GET /profiles/batch` отдаёт его (дополни
тест в `tests/test_profiles.py`).

---

## 2. `search_hq`: клиенты `user_service`

По образцу `services/notify_client.py`: синхронный `httpx`, таймаут
`settings.upstream_timeout_seconds`, при `httpx.HTTPError` — `logger.warning`
и безопасное пустое значение. **Сервис не должен падать**, если `user_service`
лежит: тревога всё равно уходит краеведу, а имена становятся запасными.

### 2.1. `services/family_client.py`

```python
def family_member_ids(user_id: str) -> list[str]:
    """GET {user_service_url}/internal/family/{user_id} с X-Internal-Key. Ошибка — []."""
```

### 2.2. `services/profile_client.py`

```python
@dataclass(frozen=True)
class ProfileBrief:
    display_name: str
    avatar_url: str | None
    city: str
    role: str
    is_verified: bool

def profile_briefs(user_ids: Iterable[str]) -> dict[str, ProfileBrief]:
    """GET {user_service_url}/profiles/batch?ids=a,b,c (публичная, без ключа).

    Дубли и пустые id отбрасываются. Больше 200 id — несколькими запросами по
    200 (лимит ручки). Ошибка — {} для всех. Нет профиля — нет ключа в словаре.
    """
```

Пустой `display_name` в профиле (человек не заполнил) считай отсутствием
имени: вызывающий код подставит запасное.

В `tests/conftest.py` добавь autouse-фикстуру, которая подменяет оба клиента
заглушками (`family_member_ids` → `[]`, `profile_briefs` → `{}`), как это
сделано для `notify_client`: тесты не должны ходить в сеть. Тесты, которым
важна семья или имена, подставляют свои словари через `monkeypatch`.

**Важно про импорт.** Сервисы зовут клиентов через модуль
(`from services import family_client` → `family_client.family_member_ids(...)`),
а не `from services.family_client import family_member_ids`: иначе
`monkeypatch` модуля не подменит уже импортированное имя.

---

## 3. `search_hq`: «Я потерялся»

### 3.1. Настройки (`core/config.py`)

```python
# --- «Я потерялся» ---
# Сколько живёт тревога, если её никто не закрыл: прогулка столько не длится,
# а висящий «поиск» через полдня только пугает.
lost_alert_ttl_minutes: int = 120
```

### 3.2. Модели (`core/models/lost_alert.py`, зарегистрируй в `core/models/__init__.py`)

```python
class LostAlertStatus(str, enum.Enum):
    active = "active"
    found = "found"
    cancelled = "cancelled"
    expired = "expired"

# Вид тревоги — строкой, а не enum: член enum с именем `self` не заведёшь, а
# SQLAlchemy кладёт в колонку имя члена, не значение.
KIND_SELF = "self"          # сам нажал «Я потерялся»
KIND_REPORTED = "reported"  # другой нажал «Не вижу …»

class LostAlert(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "lost_alerts"
    excursion_id  -> ForeignKey("excursions.id", ondelete="CASCADE"), index
    lost_user_id  -> String(36), index
    raised_by     -> String(36)
    kind          -> String(16)   # KIND_SELF | KIND_REPORTED
    status        -> Enum(LostAlertStatus, name="lost_alert_status", native_enum=False, length=16),
                     default active, index
    message       -> String(200), default ""
    created_at    -> DateTime(timezone=True), server_default=func.now()
    resolved_at   -> DateTime(timezone=True) | None
    resolved_by   -> String(36) | None

class LostAlertWatcher(Base):
    __tablename__ = "lost_alert_watchers"
    alert_id      -> ForeignKey("lost_alerts.id", ondelete="CASCADE"), primary_key
    user_id       -> String(36), primary_key
    relation      -> String(16)  # "family" | "guide"
    responded_at  -> DateTime(timezone=True) | None
```

Статус объяви так же, как `ExcursionStatus` в `core/models/excursion.py`
(`native_enum=False`, имена членов совпадают со значениями), — в ответах
видны строки `"active"`, `"found"` и так далее.

Ищущих **сохраняем** в момент тревоги, а не вычисляем на каждый запрос:
экран тревоги опрашивает бэкенд раз в 3 секунды, и ходить каждый раз в
`user_service` за семьёй нельзя.

### 3.3. Репозиторий (`repositories/lost_alert_repository.py`)

Минимум: `get(alert_id)`, `add(alert)`, `active_for(excursion_id, lost_user_id)`,
`active_on_excursion(excursion_id) -> list`, `active_where_involved(user_id) -> list`
(потерявшийся **или** есть строка ищущего), `watchers(alert_id)`,
`get_watcher(alert_id, user_id)`, `stale_active(before: datetime) -> list`.

### 3.4. Сервис (`services/lost_alert_service.py`)

`LostAlertService(db)` с методами под ручки. Держи в нём всю логику, а в
роутере — только разбор запроса и сборку ответа. Основное:

**`raise_alert(principal, excursion_id, *, lost_user_id, lat, lon, accuracy_m, message) -> tuple[LostAlert, bool]`**
(второе значение — «создана новая»):

1. `excursion = ExcursionService(db).get(excursion_id)` (сам кинет `404 Экскурсия не найдена`).
2. Закрыть просроченное (см. «Срок» ниже), в том числе вызвать
   `WalkService(db)._settle_expiry(excursion)`: прогулка могла закончиться по
   сроку, тогда статус уже не `walking`.
3. Статус не `walking` → `Conflict("Потеряться можно только во время прогулки группы")`.
4. Определи, кто нажал:
   - `is_guide = excursion.guide_id == principal.user_id or is_staff(principal)`;
   - иначе участник группы: `registered` и `checked_in_at` не `None` (как
     `WalkService._ensure_in_group`), иначе
     `PermissionDenied("Сначала отметьтесь у краеведа — встряхните телефоны рядом")`.
5. `target = lost_user_id or principal.user_id`.
   - `target == principal.user_id` и нажал краевед →
     `Conflict("Краевед ведёт группу — ему «Я потерялся» не нужно")`. (Администратор
     без записи на экскурсию тоже сюда попадает — так и надо.)
   - `target` — не участник группы (не отмечен) или это краевед экскурсии →
     `NotFound("Этого человека нет в группе")`.
   - `target != principal.user_id`, и нажавший не краевед и не администратор →
     проверь, что `target in family_client.family_member_ids(principal.user_id)`,
     иначе `PermissionDenied("Искать можно только членов своей семьи")`.
6. Если переданы `lat`/`lon` — сохрани **позицию нажавшего** точно так же,
   как `WalkService.report_position` (upsert в `ExcursionPosition`,
   `is_guide`, `updated_at = utcnow()`). Лучше вынеси общую часть из
   `report_position` в приватный метод и зови его отсюда, а не копируй.
7. Уже есть открытая тревога на `(excursion_id, target)` → верни её и `False`.
   Больше ничего не делай, уведомлений не шли.
8. Создай `LostAlert` (`kind = KIND_SELF`, если `target == principal.user_id`,
   иначе `KIND_REPORTED`).
9. Ищущие:
   - краевед (`relation="guide"`), если он не потерявшийся;
   - члены семьи потерявшегося из `family_client.family_member_ids(target)`,
     которые сами участники группы (отмечены), кроме краеведа (он уже есть) и
     самого потерявшегося (`relation="family"`);
   - при `kind = reported` нажавший тоже ищущий (если его ещё нет в списке —
     добавь с `relation` = `"guide"` для краеведа или администратора, иначе
     `"family"`), и у него сразу `responded_at = utcnow()`.
10. `commit`, потом уведомления (после `commit`, как в `WalkService._announce`):
    - `lost_alert` — всем ищущим, кроме нажавшего; тексты из CONTRACT 1.6,
      разные для `self` и `reported`;
    - `lost_alert_searching` — потерявшемуся, если `kind = reported`.
    - Имена — из `profile_client.profile_briefs(...)`, запасные — как в
      CONTRACT 1.3.
11. Верни `(alert, True)`.

**`active_for_user(principal) -> list[LostAlert]`** — после закрытия
просроченных; новые первыми.

**`get_visible(principal, alert_id) -> LostAlert`** — `NotFound("Поиск не найден")`;
видят потерявшийся, ищущие и `is_staff`, остальным
`PermissionDenied("Этот поиск видят только семья и краевед")`. Просроченную
закрой перед ответом.

**`respond(principal, alert_id)`** — только ищущий, иначе
`PermissionDenied("Откликнуться могут только семья и краевед")` (потерявшийся
не ищущий — ему тоже `403`). Статус не `active` →
`Conflict("Поиск уже закрыт")`. Если `responded_at` пусто — поставь, `commit`
и пошли потерявшемуся `lost_alert_responding`. Повторно — ничего.

**`resolve(principal, alert_id)`** — могут потерявшийся, ищущие, `is_staff`,
иначе `PermissionDenied("Закрыть поиск могут только семья, краевед и тот, кого ищут")`.
`found` → вернуть как есть. `cancelled`/`expired` → `Conflict("Поиск уже закрыт")`.
Иначе `status = found`, `resolved_at`, `resolved_by`, `commit`,
`lost_alert_closed` (`payload.status = "found"`) всем участникам поиска
(потерявшийся + ищущие), кроме нажавшего.

**`cancel(principal, alert_id)`** — могут потерявшийся, `raised_by`,
`is_staff`, иначе
`PermissionDenied("Отменить поиск может тот, кого ищут, или тот, кто его начал")`.
`cancelled` → как есть; `found`/`expired` → `Conflict("Поиск уже закрыт")`.
Иначе `cancelled` + уведомления, как у `resolve` (`payload.status = "cancelled"`).

**Срок.** `expire_stale()` переводит в `expired` все `active` старше
`lost_alert_ttl_minutes` (`resolved_at = utcnow()`, `resolved_by = None`,
**без** уведомлений). Зови в начале каждого публичного метода — так же, как
`_settle_expiry` в прогулке: фонового планировщика в проекте нет намеренно.
Отдельно `expire_for_excursion(excursion_id)` — все открытые тревоги
экскурсии в `expired`.

**`has_active(excursion_id) -> bool`** — для блокировки завершения.

Будь внимателен к круговым импортам: `WalkService` будет звать
`LostAlertService`, а `LostAlertService` — `WalkService`. Разорви цикл так,
чтобы общие вещи (запрос «есть ли открытая тревога», «закрыть тревоги
экскурсии», запись позиции) жили в репозиториях или в модульных функциях,
которые импортируют обе стороны, либо импортируй внутри метода — но выбери
одно и объясни в комментарии.

### 3.5. Сборка ответа `LostAlert`

Схемы — `api/schemas/lost_alert.py` (Pydantic, `UtcDatetime` из
`api/schemas/excursion.py` для всех дат). Поля и порядок `watchers` — ровно
как в CONTRACT 1.3:

- позиции берутся из `ExcursionPosition` **без** фильтра
  `walk_position_ttl_seconds` (с `updated_at`);
- `distance_m = round(core.geo.distance_m(...))`, если есть обе точки;
- сортировка ищущих: откликнувшиеся первыми, дальше по `distance_m`
  (`None` в конце), при равенстве — по `user_id`;
- имена одним вызовом `profile_client.profile_briefs` на всех людей тревоги;
- `my_role`: `"lost"` / `"watcher"` / `"observer"` (последнее — администратор
  не из списка);
- `excursion_title` — `Excursion.title`.

Собирать ответ удобно в сервисе в dataclass-«вид» (как `WalkState`) и
превращать его в схему в роутере `from_view`-методом.

### 3.6. Роутер (`api/routers/lost_alerts.py`)

Один `APIRouter(tags=["lost-alerts («Я потерялся»)"])` без префикса и пути
полностью:

| Метод и путь | Код | Тело |
|---|---|---|
| `POST /excursions/{excursion_id}/lost` | `201` новая / `200` уже была | `LostAlertCreate` |
| `GET /lost-alerts/active` | `200` | — |
| `GET /lost-alerts/{alert_id}` | `200` | — |
| `POST /lost-alerts/{alert_id}/respond` | `200` | — |
| `POST /lost-alerts/{alert_id}/resolve` | `200` | — |
| `POST /lost-alerts/{alert_id}/cancel` | `200` | — |

Код `201/200` в одной ручке — через параметр `response: Response` и
`response.status_code = …`. `GET /lost-alerts/active` объяви **раньше**
`GET /lost-alerts/{alert_id}`, иначе `active` поймается как id. Подключи
роутер в `api/routers/__init__.py`, зависимость `LostAlertServiceDep` — в
`api/deps.py` по образцу остальных.

`LostAlertCreate`: `lost_user_id: str | None = Field(default=None, max_length=36)`,
`lat: float | None = Field(default=None, ge=-90, le=90)`,
`lon: float | None = Field(default=None, ge=-180, le=180)`,
`accuracy_m: float | None = Field(default=None, ge=0, le=10000)`,
`message: str = Field(default="", max_length=200)` (обрежь пробелы).
`lat` без `lon` или наоборот — `422` (`model_validator`).

### 3.7. Изменения в прогулке и экскурсиях

- `WalkService.finish` и `ExcursionService.cancel`: если на экскурсии есть
  открытая тревога → `Conflict("Кто-то из группы потерялся — сначала найдите его или закройте поиск")`.
  Проверку делай **до** смены статуса.
- `WalkService._close_if_expired`: когда прогулка закрывается по сроку —
  закрыть и её тревоги (`expired`).
- `GroupMember` / `GroupMemberOut`: новое поле `lost_alert_id: str | None`
  (в схеме — со значением по умолчанию `None`). Заполняй в
  `WalkService.state` одним запросом открытых тревог экскурсии.

### 3.8. Тесты (`tests/test_lost_alerts.py`)

Используй готовые помощники из `tests/test_walk.py`
(`gathered`, `lead`, `report`) и `tests/test_excursions.py`. Семью подставляй
через `monkeypatch` на `family_client.family_member_ids`
(`lambda user_id: {...}.get(user_id, [])`), имена — на
`profile_client.profile_briefs`. Минимальный набор:

1. Участник жмёт «Я потерялся» на прогулке → `201`, `kind=self`,
   `my_role=lost`; ищущие — краевед и член семьи из группы; член семьи **не**
   из группы в ищущие не попал; уведомление `lost_alert` ушло ровно
   ищущим с текстами из контракта.
2. Повторное нажатие → `200`, тот же `id`, уведомлений не добавилось.
3. До выхода группы (сбор) → `409` с текстом из контракта; не отметившийся →
   `403`; краевед за себя → `409`.
4. «Не вижу»: член семьи → `201`, `kind=reported`, нажавший в ищущих с
   `responding=true`, потерявшемуся ушло `lost_alert_searching`; чужой
   (не семья) → `403`; краевед за любого участника → `201`; по не участнику → `404`.
5. `lat/lon` в теле пишутся в позицию нажавшего: `GET …/walk` её видит.
6. `respond`: `responding` стало `true`, потерявшемуся одно
   `lost_alert_responding`, повтор — без нового уведомления; потерявшийся и
   посторонний → `403`.
7. `resolve` → `found`, `resolved_by`; `lost_alert_closed` всем, кроме
   нажавшего; повтор → `200`; `cancel` после `found` → `409`.
8. `cancel` потерявшимся → `cancelled`; ищущим, который не поднимал тревогу, → `403`.
9. `GET /lost-alerts/{id}` посторонним → `403`; `GET /lost-alerts/active`
   видит тревогу потерявшийся и ищущий, посторонний — пустой список.
10. Позиции и расстояние: после `report` обоих — `lost.position`,
    `watchers[].distance_m` и сортировка (откликнувшийся первым).
11. Срок: сдвинь `created_at` в прошлое (прямо в БД через сессию) или
    `monkeypatch` на `settings.lost_alert_ttl_minutes = 0` → статус `expired`,
    в `active` не видно, уведомлений нет.
12. Блокировка: при открытой тревоге `walk/finish` и `cancel` → `409`; после
    `resolve` — проходят.
13. `GET …/walk`: у потерявшегося в `members[]` `lost_alert_id` = id тревоги,
    у остальных `null`.
14. `user_service` недоступен (клиенты вернули пусто) → тревога создаётся,
    ищущий — только краевед, имена — запасные.

---

## 4. `search_hq`: рейтинг краеведов (ветка `feat/guide-rating-api`)

### 4.1. Настройки

```python
# --- рейтинг краеведов ---
# Байесовское среднее: сколько «виртуальных» оценок добавляем каждому и какого
# они балла (середина шкалы — почему не общее среднее, см. CONTRACT 2.2).
guide_rating_prior_weight: int = 5
guide_rating_prior_mean: float = 3.0
```

### 4.2. Репозиторий (`repositories/rating_repository.py`)

- `per_guide(since: datetime | None) -> list[Row]` — одним `GROUP BY guide_id`:
  `guide_id`, `count`, `sum(rating)`, `avg(rating)`, `max(created_at)`; с
  `since` — только оценки не раньше него.
- `global_average(since) -> float | None`.
- `distribution(guide_id) -> dict[int, int]`.
- `recent_for_guide` уже есть.
- В `ExcursionRepository`: `finished_count_by_guide(guide_ids) -> dict[str, int]`
  (одним `GROUP BY`, статус `finished`).

### 4.3. Сервис (`services/rating_service.py`)

- `leaderboard(principal | None, *, period, limit, offset)`:
  1. `since = utcnow() - timedelta(days=30)` для `month`, `None` для `all`.
  2. Нет оценок — пустой ответ (`global_average: 0`, `total: 0`, `items: []`);
     `global_average` — среднее всех оценок периода, только для сведения.
  3. Для каждого краеведа `score = (C*M + sum) / (C + count)`, `M` — настройка
     `guide_rating_prior_mean`.
  4. Сортировка из CONTRACT 2.2, места — порядковый номер после сортировки,
     **до** `offset/limit` (на второй странице первое место — 51-е).
  5. Для строк страницы — `excursions_led` и профили одним вызовом
     `profile_client.profile_briefs`.
  6. Округление: `average` — 2 знака, `score` — 3, `global_average` — 2.
- Общую часть «посчитать все места за период» вынеси в функцию: она же нужна
  карточке краеведа, чтобы узнать его `place` и `total_ranked`.
- `guide_summary` расширь до полей CONTRACT 2.4. У `recent` добавь
  `rater_name`, `rater_avatar_url` (профили одним вызовом на всех оценщиков) и
  `excursion_title` (названия экскурсий одним запросом по их id).

Считать рейтинг в Python по уже сгруппированным в SQL строкам нормально:
краеведов — десятки, а не миллионы. Не тяни в память все оценки.

### 4.4. API

- `api/routers/guides.py`: `GET /guides/rating` (параметры `period:
  Literal["all", "month"] = "all"`, `limit: int = Query(50, ge=1, le=100)`,
  `offset: int = Query(0, ge=0)`, `OptionalPrincipal` для `is_me`).
  Расширь `GuideRatingSummaryOut` новыми полями — **только добавлением**:
  старые поля и их смысл не меняются, на них завязан веб
  (`frontend/web/src/modules/excursions/components/GuideRatingList.vue`).
- `api/routers/excursions.py`: в `list_excursions` новый параметр
  `guide_id: Annotated[str | None, Query(max_length=36)] = None` → в
  `service.search(...)`. Репозиторий фильтр уже умеет.
- Схемы — в `api/schemas/rating.py`: `GuideRankOut`, `GuideLeaderboardOut`,
  `GuideProfileOut`, `GuideReviewOut` (= `GuideRatingOut` + три поля).

### 4.5. Уведомление «Оцените экскурсию»

В `ExcursionService._credit_excursion_completion` (её зовут все пути
завершения) после начисления статистики отправь `rate_excursion` отмеченным
участникам со статусом `registered`, тексты — из CONTRACT 2.6. Нет таких —
не шли. Проверь существующие тесты, где фикстура `sent` считает уведомления:
если какой-то тест теперь видит лишнее `rate_excursion`, поправь тест
осознанно (сравнивай только нужный `kind`), а не выключай рассылку.

### 4.6. Тесты (`tests/test_guide_leaderboard.py` + дополнения в `tests/test_ratings.py`)

Оценки удобно заводить прямо в БД (`GuideRating(...)` через сессию из
`core.db.SessionLocal`), чтобы не проводить каждую экскурсию через бамп.

1. Порядок по байесу: краевед A — одна 5, краевед B — 20 оценок со средним
   4,8 → B выше A. Проверь `score` по формуле руками в тесте.
2. `period=month`: оценка 40-дневной давности не учитывается, краевед только
   со старыми оценками в месячный рейтинг не попадает.
3. `limit/offset`: места сквозные, `total` — все.
4. `is_me` с токеном; без токена у всех `false`.
5. Имена из `profile_client`; без профиля — `"Краевед"`, `null`, `""`, `false`.
6. `excursions_led` считает только `finished`.
7. `GET /guides/{id}/rating`: новые поля, `distribution` со всеми пятью
   ключами, `place/total_ranked` совпадают с таблицей; у краеведа без оценок
   `score = place = null`; старые поля не изменились.
8. `GET /excursions?guide_id=…` отдаёт только его экскурсии.
9. Завершение прогулки шлёт `rate_excursion` отмеченным и не шлёт
   записавшимся, но не пришедшим; то же при закрытии сбора и по сроку.
10. `period=week` → `422`, `limit=0` → `422`.

---

## Как проверять

```bash
cd backend/search_hq_service && uv run pytest -q
cd backend/user_service && uv run pytest -q
```

Все тесты обоих сервисов зелёные — обязательное условие. Потом руками через
Swagger (`uv run uvicorn main:app --port 8004`, открыть `/docs`) пройди
сценарий из контракта: экскурсия → запись → сбор → бамп → прогулка →
«Я потерялся» → «Иду» → «Нашлись».

## В конце

Отчёт человеку: что сделано по разделам, отличия от контракта (если были, с
причиной и предложенной правкой `CONTRACT.md`), что проверено тестами и что
руками. На проде новые таблицы появятся сами при старте сервиса, миграций
не нужно.
