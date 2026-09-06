import os
import tempfile

# Настроить окружение ДО импорта app-модулей.
_db_fd, _db_path = tempfile.mkstemp(suffix=".sqlite")
os.close(_db_fd)
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///" + _db_path.replace("\\", "/")
os.environ["JWT_SECRET"] = "test-secret-test-secret-test-secret-0123456789"
os.environ["APP_ENV"] = "test"
os.environ.pop("BOOTSTRAP_ROOT_EMAIL", None)
os.environ.pop("BOOTSTRAP_ROOT_PASSWORD", None)

import pytest
from fastapi.testclient import TestClient

import main
from core.db import engine
from core.models import Base


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(main.app) as c:
        yield c


def pytest_sessionfinish(session, exitstatus):
    try:
        os.unlink(_db_path)
    except OSError:
        pass
