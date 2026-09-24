from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from core.config import settings
from services.external.registry import vk_provider, yandex_provider

RETURN_TO = "marshruty://auth/external"


@pytest.fixture()
def mock_mode(monkeypatch):
    monkeypatch.setattr(settings, "external_auth_mock", True)


def start(client, provider, return_to=RETURN_TO):
    body = {"return_to": return_to} if return_to is not None else {}
    return client.post(f"/auth/external/{provider}/start", json=body)


def callback(client, provider, **params):
    return client.get(f"/auth/external/{provider}/callback", params=params, follow_redirects=False)


def state_of(authorize_url: str) -> str:
    return parse_qs(urlparse(authorize_url).query)["state"][0]


def returned(response) -> dict[str, str]:
    """Параметры, с которыми человека вернули в приложение."""
    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith(RETURN_TO + "?")
    return {key: values[0] for key, values in parse_qs(urlparse(location).query).items()}


def complete(client, login_id, result_code=None):
    body = {"login_id": login_id}
    if result_code is not None:
        body["result_code"] = result_code
    return client.post("/auth/external/complete", json=body)


# --- какие способы входа есть ---


def test_providers_disabled_without_settings(client):
    providers = {p["provider"]: p for p in client.get("/auth/external/providers").json()}
    assert set(providers) == {"vk", "yandex", "max", "gosuslugi"}
    assert not any(p["enabled"] for p in providers.values())
    assert providers["max"]["kind"] == "bot"


def test_gosuslugi_not_configured_explains_why(client):
    response = start(client, "gosuslugi")
    assert response.status_code == 503
    assert "ЕСИА" in response.json()["detail"]


def test_mock_mode_enables_all_providers(client, mock_mode):
    providers = client.get("/auth/external/providers").json()
    assert all(p["enabled"] and p["mock"] and p["kind"] == "redirect" for p in providers)


# --- вход через тестовый провайдер: весь путь ---


def test_mock_login_full_flow(client, mock_mode):
    started = start(client, "vk")
    assert started.status_code == 201
    login = started.json()
    assert "/auth/external/mock/authorize" in login["authorize_url"]

    # Пока человек не подтвердил вход — токенов нет.
    assert complete(client, login["login_id"]).status_code == 202

    page = client.get(login["authorize_url"].split("8001", 1)[-1])
    assert page.status_code == 200
    assert "Тестовый вход через VK ID" in page.text

    back = returned(
        callback(client, "vk", state=state_of(login["authorize_url"]), code="mock", mock_name="Анна")
    )
    assert back["provider"] == "vk"
    assert "access_token" not in back  # токены в URL не попадают

    # login_id без одноразового кода с устройства не отдаёт токены.
    assert complete(client, login["login_id"]).status_code == 403

    done = complete(client, login["login_id"], back["result_code"])
    assert done.status_code == 200
    body = done.json()
    assert body["display_name"] == "Анна"
    assert body["is_new_user"] is True
    assert body["user"]["role"] == "family"
    assert body["user"]["email"].endswith("@external.marshruty.ru")

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["id"] == body["user"]["id"]

    # Второй раз по той же попытке токены не выдаются.
    assert complete(client, login["login_id"], back["result_code"]).status_code == 410


def test_same_provider_account_logs_into_same_user(client, mock_mode):
    user_ids = []
    for expected_new in (True, False):
        login = start(client, "max").json()
        back = returned(
            callback(client, "max", state=state_of(login["authorize_url"]), code="mock", mock_name="Пётр")
        )
        body = complete(client, login["login_id"], back["result_code"]).json()
        assert body["is_new_user"] is expected_new
        user_ids.append(body["user"]["id"])
    assert user_ids[0] == user_ids[1]


def test_refusal_at_provider_fails_login(client, mock_mode):
    login = start(client, "vk").json()
    back = returned(callback(client, "vk", state=state_of(login["authorize_url"]), error="access_denied"))
    assert "error" in back

    failed = complete(client, login["login_id"])
    assert failed.status_code == 400
    assert "не подтверждён" in failed.json()["detail"]


def test_unknown_state_shows_page(client, mock_mode):
    response = callback(client, "vk", state="nope", code="mock")
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]


def test_expired_login(client, mock_mode, monkeypatch):
    monkeypatch.setattr(settings, "external_auth_login_ttl_seconds", -1)
    login = start(client, "vk").json()
    assert complete(client, login["login_id"]).status_code == 410


# --- куда можно вернуть человека ---


@pytest.mark.parametrize(
    "return_to",
    ["https://evil.example/steal", "https://localhost.evil.example/", "javascript:alert(1)"],
)
def test_foreign_return_to_rejected(client, mock_mode, return_to):
    assert start(client, "vk", return_to=return_to).status_code == 400


def test_redirect_provider_requires_return_to(client, mock_mode):
    assert start(client, "vk", return_to=None).status_code == 400


def test_mock_page_hidden_without_mock_mode(client):
    assert client.get("/auth/external/mock/authorize", params={"provider": "vk", "state": "x"}).status_code == 404


def test_mock_never_in_production(client, mock_mode, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    assert start(client, "vk").status_code == 503


# --- VK ID по-настоящему, сеть подменена ---


def test_vk_id_exchange(client, monkeypatch):
    monkeypatch.setattr(settings, "vk_id_client_id", "54321")
    seen = {}

    def vk_api(request: httpx.Request) -> httpx.Response:
        form = parse_qs(request.content.decode())
        if request.url.path == "/oauth2/auth":
            seen["token_request"] = form
            return httpx.Response(200, json={"access_token": "vk-token", "user_id": 777})
        if request.url.path == "/oauth2/user_info":
            assert form["access_token"] == ["vk-token"]
            return httpx.Response(
                200,
                json={"user": {"user_id": "777", "first_name": "Иван", "last_name": "Орлов", "email": "i@vk.example"}},
            )
        return httpx.Response(404)

    monkeypatch.setattr(vk_provider, "transport", httpx.MockTransport(vk_api))

    login = start(client, "vk").json()
    authorize = urlparse(login["authorize_url"])
    query = parse_qs(authorize.query)
    assert authorize.netloc == "id.vk.com"
    assert query["code_challenge_method"] == ["S256"]
    assert query["redirect_uri"] == ["http://127.0.0.1:8001/auth/external/vk/callback"]

    back = returned(callback(client, "vk", state=query["state"][0], code="vk-code", device_id="dev-1"))
    token_request = seen["token_request"]
    assert token_request["code"] == ["vk-code"]
    assert token_request["device_id"] == ["dev-1"]
    assert len(token_request["code_verifier"][0]) >= 43

    body = complete(client, login["login_id"], back["result_code"]).json()
    assert body["display_name"] == "Иван Орлов"
    assert body["user"]["email"] == "vk-777@external.marshruty.ru"


def test_vk_id_error_fails_login(client, monkeypatch):
    monkeypatch.setattr(settings, "vk_id_client_id", "54321")
    monkeypatch.setattr(
        vk_provider,
        "transport",
        httpx.MockTransport(lambda _: httpx.Response(400, json={"error": "invalid_grant"})),
    )
    login = start(client, "vk").json()
    back = returned(callback(client, "vk", state=state_of(login["authorize_url"]), code="bad"))
    assert "invalid_grant" in back["error"]


# --- Яндекс ID по-настоящему, сеть подменена ---


@pytest.fixture()
def yandex_app(monkeypatch):
    monkeypatch.setattr(settings, "yandex_id_client_id", "ya-client")
    monkeypatch.setattr(settings, "yandex_id_client_secret", "ya-secret")


def test_yandex_needs_client_secret(client, monkeypatch):
    monkeypatch.setattr(settings, "yandex_id_client_id", "ya-client")
    response = start(client, "yandex")
    assert response.status_code == 503
    assert "YANDEX_ID_CLIENT_SECRET" in response.json()["detail"]


def test_yandex_id_exchange(client, yandex_app, monkeypatch):
    seen = {}

    def yandex_api(request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth.yandex.ru" and request.url.path == "/token":
            seen["token_request"] = parse_qs(request.content.decode())
            return httpx.Response(200, json={"access_token": "ya-token", "token_type": "bearer"})
        if request.url.host == "login.yandex.ru" and request.url.path == "/info":
            assert request.headers["Authorization"] == "OAuth ya-token"
            return httpx.Response(
                200,
                json={
                    "id": "1130000012345678",
                    "login": "ivan.orlov",
                    "real_name": "Иван Орлов",
                    "default_email": "ivan.orlov@yandex.ru",
                    "default_avatar_id": "131652443",
                    "is_avatar_empty": False,
                },
            )
        return httpx.Response(404)

    monkeypatch.setattr(yandex_provider, "transport", httpx.MockTransport(yandex_api))

    login = start(client, "yandex").json()
    authorize = urlparse(login["authorize_url"])
    query = parse_qs(authorize.query)
    assert authorize.netloc == "oauth.yandex.ru"
    assert query["client_id"] == ["ya-client"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["redirect_uri"] == ["http://127.0.0.1:8001/auth/external/yandex/callback"]

    back = returned(callback(client, "yandex", state=query["state"][0], code="ya-code"))
    token_request = seen["token_request"]
    assert token_request["code"] == ["ya-code"]
    assert token_request["client_secret"] == ["ya-secret"]
    assert len(token_request["code_verifier"][0]) >= 43

    body = complete(client, login["login_id"], back["result_code"]).json()
    assert body["display_name"] == "Иван Орлов"
    assert body["user"]["email"] == "yandex-1130000012345678@external.marshruty.ru"


def test_yandex_id_error_fails_login(client, yandex_app, monkeypatch):
    monkeypatch.setattr(
        yandex_provider,
        "transport",
        httpx.MockTransport(
            lambda _: httpx.Response(400, json={"error": "bad_verification_code", "error_description": "Code has expired"})
        ),
    )
    login = start(client, "yandex").json()
    back = returned(callback(client, "yandex", state=state_of(login["authorize_url"]), code="bad"))
    assert "Code has expired" in back["error"]


# --- MAX через бота ---


@pytest.fixture()
def max_bot(monkeypatch):
    monkeypatch.setattr(settings, "max_bot_name", "marshruty_bot")
    monkeypatch.setattr(settings, "max_webhook_secret", "bot-secret")


def webhook(client, update, secret="bot-secret"):
    return client.post(
        "/auth/external/max/webhook", json=update, headers={settings.max_webhook_secret_header: secret}
    )


def test_max_bot_flow(client, max_bot):
    started = start(client, "max", return_to=None)
    assert started.status_code == 201
    login = started.json()
    assert login["kind"] == "bot"
    assert login["authorize_url"].startswith("https://max.ru/marshruty_bot?start=")
    payload = login["authorize_url"].split("start=", 1)[1]

    assert complete(client, login["login_id"]).status_code == 202
    assert webhook(client, {"update_type": "bot_started", "payload": payload, "user": {"user_id": 42}}, secret="wrong").status_code == 403

    handled = webhook(
        client, {"update_type": "bot_started", "payload": payload, "user": {"user_id": 42, "name": "Мария"}}
    )
    assert handled.json() == {"ok": True, "handled": True}

    body = complete(client, login["login_id"]).json()
    assert body["display_name"] == "Мария"
    assert body["user"]["email"] == "max-42@external.marshruty.ru"


def test_max_ignores_unrelated_updates(client, max_bot):
    response = webhook(client, {"update_type": "message_created", "message": {"body": {"text": "привет"}}})
    assert response.json() == {"ok": True, "handled": False}
