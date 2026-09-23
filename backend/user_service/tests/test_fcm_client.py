import json

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from core.config import settings
from services import fcm_client

# jwt.encode(..., algorithm="RS256") требует настоящий валидный RSA-ключ —
# содержимое подписи в тесте не проверяется, но парситься он должен.
_TEST_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_TEST_KEY_PEM = _TEST_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode()

def _response(status: int, url: str, json_body: dict) -> httpx.Response:
    """httpx.Response без привязанного request не умеет raise_for_status()."""
    return httpx.Response(status, json=json_body, request=httpx.Request("POST", url))


FAKE_SERVICE_ACCOUNT = {
    "type": "service_account",
    "project_id": "marshruty-demo",
    "private_key": _TEST_KEY_PEM,
    "client_email": "fcm-sender@marshruty-demo.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
}


@pytest.fixture(autouse=True)
def reset_token_cache():
    fcm_client._cached_token = None
    fcm_client._cached_token_expires_at = 0.0
    yield
    fcm_client._cached_token = None
    fcm_client._cached_token_expires_at = 0.0


@pytest.fixture()
def configured(monkeypatch):
    monkeypatch.setattr(settings, "fcm_project_id", "marshruty-demo")
    monkeypatch.setattr(settings, "fcm_credentials_json", json.dumps(FAKE_SERVICE_ACCOUNT))
    monkeypatch.setattr(settings, "fcm_credentials_path", None)


def test_not_configured_without_project_id(monkeypatch):
    monkeypatch.setattr(settings, "fcm_project_id", None)
    assert fcm_client.is_configured() is False


def test_not_configured_without_credentials(monkeypatch):
    monkeypatch.setattr(settings, "fcm_project_id", "marshruty-demo")
    monkeypatch.setattr(settings, "fcm_credentials_json", None)
    monkeypatch.setattr(settings, "fcm_credentials_path", None)
    assert fcm_client.is_configured() is False


def test_configured_with_inline_json(configured):
    assert fcm_client.is_configured() is True


def test_send_ok(configured, monkeypatch):
    calls = []

    def fake_post(url, **kw):
        calls.append((url, kw))
        if "oauth2.googleapis.com" in url:
            return _response(200, url, {"access_token": "at-1", "expires_in": 3600})
        return _response(200, url, {"name": "projects/x/messages/1"})

    monkeypatch.setattr(httpx, "post", fake_post)

    result = fcm_client.send(token="dev-tok", title="Заголовок", body="Текст", data={"kind": "achievement"})
    assert result is fcm_client.SendResult.ok

    token_call, send_call = calls
    assert token_call[0] == "https://oauth2.googleapis.com/token"
    assert send_call[0] == "https://fcm.googleapis.com/v1/projects/marshruty-demo/messages:send"
    assert send_call[1]["headers"]["Authorization"] == "Bearer at-1"
    assert send_call[1]["json"]["message"]["token"] == "dev-tok"
    assert send_call[1]["json"]["message"]["data"] == {"kind": "achievement"}


def test_send_caches_access_token_between_calls(configured, monkeypatch):
    token_calls = []

    def fake_post(url, **kw):
        if "oauth2.googleapis.com" in url:
            token_calls.append(1)
            return _response(200, url, {"access_token": "at-1", "expires_in": 3600})
        return _response(200, url, {})

    monkeypatch.setattr(httpx, "post", fake_post)

    fcm_client.send(token="tok-1", title="t", body="b")
    fcm_client.send(token="tok-2", title="t", body="b")
    assert len(token_calls) == 1


def test_send_unregistered_token_is_token_invalid(configured, monkeypatch):
    def fake_post(url, **kw):
        if "oauth2.googleapis.com" in url:
            return _response(200, url, {"access_token": "at-1", "expires_in": 3600})
        return _response(
            404,
            url,
            {
                "error": {
                    "code": 404,
                    "status": "NOT_FOUND",
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.firebase.fcm.v1.FcmError",
                            "errorCode": "UNREGISTERED",
                        }
                    ],
                }
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    assert fcm_client.send(token="dead", title="t", body="b") is fcm_client.SendResult.token_invalid


def test_send_other_failure_is_failed(configured, monkeypatch):
    def fake_post(url, **kw):
        if "oauth2.googleapis.com" in url:
            return _response(200, url, {"access_token": "at-1", "expires_in": 3600})
        return _response(500, url, {"error": {"code": 500, "status": "INTERNAL"}})

    monkeypatch.setattr(httpx, "post", fake_post)

    assert fcm_client.send(token="tok", title="t", body="b") is fcm_client.SendResult.failed


def test_send_without_configuration_is_failed():
    assert fcm_client.send(token="tok", title="t", body="b") is fcm_client.SendResult.failed


def test_send_when_token_exchange_fails(configured, monkeypatch):
    def fake_post(url, **kw):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx, "post", fake_post)

    assert fcm_client.send(token="tok", title="t", body="b") is fcm_client.SendResult.failed
