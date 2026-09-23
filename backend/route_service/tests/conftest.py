import os
import tempfile
import time
import uuid

_db_fd, _db_path = tempfile.mkstemp(suffix=".sqlite")
os.close(_db_fd)
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///" + _db_path.replace("\\", "/")
os.environ["JWT_SECRET"] = "test-secret-test-secret-test-secret-0123456789"
os.environ["APP_ENV"] = "test"

import jwt
import pytest
from fastapi.testclient import TestClient

import main
from core.db import engine
from core.models import Base

SECRET = os.environ["JWT_SECRET"]


def make_token(*, user_id: str | None = None, role: str = "family", is_root: bool = False) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "sub": user_id or str(uuid.uuid4()),
            "role": role,
            "is_root": is_root,
            "iss": "auth_service",
            "iat": now,
            "exp": now + 900,
            "typ": "access",
        },
        SECRET,
        algorithm="HS256",
    )


def auth_header(**kwargs) -> dict:
    return {"Authorization": f"Bearer {make_token(**kwargs)}"}


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(main.app) as c:
        yield c


@pytest.fixture()
def author_header():
    return auth_header(user_id="author-1", role="local_historian")


@pytest.fixture(autouse=True)
def no_real_achievement_calls(monkeypatch):
    """По умолчанию не ходим в сеть за user_service — тесты не про ачивки/
    статистику делают это на каждом complete-waypoint."""
    import services.progress_service as progress_service_module

    monkeypatch.setattr(progress_service_module, "award_achievement", lambda **kw: None)
    monkeypatch.setattr(progress_service_module, "increment_stat", lambda **kw: None)


def pytest_sessionfinish(session, exitstatus):
    try:
        os.unlink(_db_path)
    except OSError:
        pass
