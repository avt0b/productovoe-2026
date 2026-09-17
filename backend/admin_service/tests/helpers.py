"""Общие тестовые двойники для дашборда и операций.

`Upstream` в проде реально ходит по HTTP на другие сервисы через
`httpx.AsyncClient`. В тестах моков транспорта нет (см. pyproject.toml —
только `httpx`, без respx), поэтому вместо мока транспорта подменяется сама
FastAPI-зависимость `get_upstream` (см. `api/deps.py`) через
`app.dependency_overrides`. Сама фикстура `fake_upstream` живёт в
`tests/conftest.py` (а не здесь) — так её можно использовать в тестовых
модулях без импорта по имени, которое совпадает с именем параметра фикстуры
в каждом тесте (иначе ruff справедливо ругается на F811).

Здесь — только то, что импортируется явно и используется как обычный код:
класс `FakeUpstream` и фабрика `create_admin`.
"""

from core import security
from core.db import SessionLocal
from core.models import AdminRole, AdminUser


def create_admin(
    email: str,
    password: str,
    role: AdminRole,
    full_name: str = "Тестовый администратор",
) -> AdminUser:
    """Создаёт администратора с заданной ролью — по аналогии с фикстурой `superadmin`."""
    with SessionLocal() as db:
        admin = AdminUser(
            email=email,
            password_hash=security.hash_password(password),
            full_name=full_name,
            role=role,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        db.expunge(admin)
        return admin


class FakeUpstream:
    """Двойник `services.upstream.Upstream` с теми же сигнатурами методов.

    Все обращения к `call()` записываются в `self.calls`, чтобы тест мог
    проверить, что дошло до "сервиса" (service/method/path/actor_id/params/json).
    Ответ на конкретный вызов задаётся через `set_response`/`fail` по ключу
    (service, method, path) — этого достаточно, т.к. в каждом тесте на один
    маршрут приходится один вызов с этим ключом.
    """

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self._responses: dict[tuple[str, str, str], object] = {}
        self.stats: dict[str, dict] = {}
        self.health: list[dict] = []

    def set_response(self, service: str, method: str, path: str, value) -> None:
        self._responses[(service, method, path)] = value

    def fail(self, service: str, method: str, path: str, detail: str = "Сервис недоступен") -> None:
        from core.exceptions import UpstreamUnavailable

        self._responses[(service, method, path)] = UpstreamUnavailable(detail)

    async def call(
        self,
        service: str,
        method: str,
        path: str,
        *,
        actor_id: str | None = None,
        params: dict | None = None,
        json: dict | None = None,
    ):
        self.calls.append(
            {
                "service": service,
                "method": method,
                "path": path,
                "actor_id": actor_id,
                "params": params,
                "json": json,
            }
        )
        key = (service, method, path)
        if key not in self._responses:
            raise AssertionError(f"FakeUpstream: незапланированный вызов {key}")
        value = self._responses[key]
        if isinstance(value, Exception):
            raise value
        return value

    async def request(self, *args, **kwargs):  # pragma: no cover - не используется в тестах
        raise NotImplementedError("FakeUpstream.request не используется операциями/дашбордом")

    async def all_stats(self) -> dict[str, dict]:
        return self.stats

    async def all_health(self) -> list[dict]:
        return self.health
