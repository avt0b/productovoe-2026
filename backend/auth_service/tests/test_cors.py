def test_client_origins_allowed(client):
    # Клиентское приложение: dev-сервер Vite и APK на Capacitor (https://localhost,
    # на стенде с сервисами по http — http://localhost).
    for origin in ("http://localhost:5174", "https://localhost", "http://localhost"):
        response = client.options(
            "/auth/login",
            headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin


def test_foreign_origin_rejected(client):
    response = client.options(
        "/auth/login",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in response.headers


def test_login_response_carries_cors_header(client):
    client.post("/auth/register", json={"email": "guide@marshruty.ru", "password": "pass-1234"})
    response = client.post(
        "/auth/login",
        json={"email": "guide@marshruty.ru", "password": "pass-1234"},
        headers={"Origin": "https://localhost"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://localhost"
