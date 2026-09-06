import os

os.environ["JWT_SECRET"] = "test-secret-test-secret-test-secret-0123456789"
os.environ["APP_ENV"] = "test"

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture()
def client():
    with TestClient(main.app) as c:
        yield c
