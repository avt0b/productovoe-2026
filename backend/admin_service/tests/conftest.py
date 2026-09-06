import os
import tempfile

# Настроить окружение ДО импорта app-модулей.
_db_fd, _db_path = tempfile.mkstemp(suffix=".sqlite")
os.close(_db_fd)
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///" + _db_path.replace("\\", "/")
os.environ["ADMIN_JWT_SECRET"] = "test-admin-secret-test-admin-secret-0123456789"
os.environ["INTERNAL_API_KEY"] = "test-internal-key"
os.environ["APP_ENV"] = "test"
# Тесты входа проверяют оба режима, поэтому политику включаем точечно.
os.environ["REQUIRE_TOTP"] = "false"
os.environ.pop("BOOTSTRAP_ADMIN_EMAIL", None)
os.environ.pop("BOOTSTRAP_ADMIN_PASSWORD", None)

import pytest
from fastapi.testclient import TestClient

import main
from core import security
from core.db import SessionLocal, engine
from core.models import AdminRole, AdminUser, Base

SUPERADMIN = {"email": "root@marshruty.ru", "password": "correct-horse-battery"}


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(main.app) as c:
        yield c


@pytest.fixture()
def superadmin(client) -> AdminUser:
    with SessionLocal() as db:
        admin = AdminUser(
            email=SUPERADMIN["email"],
            password_hash=security.hash_password(SUPERADMIN["password"]),
            full_name="Тестовый суперадмин",
            role=AdminRole.superadmin,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        db.expunge(admin)
        return admin


def login(client, email: str = SUPERADMIN["email"], password: str = SUPERADMIN["password"]):
    return client.post("/admin/auth/login", json={"email": email, "password": password})


def auth_headers(client, **kwargs) -> dict[str, str]:
    body = login(client, **kwargs).json()
    return {"Authorization": f"Bearer {body['access_token']}"}


def pytest_sessionfinish(session, exitstatus):
    try:
        os.unlink(_db_path)
    except OSError:
        pass
