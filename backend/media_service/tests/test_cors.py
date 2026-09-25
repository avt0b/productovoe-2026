import pytest


@pytest.mark.parametrize(
    "origin", ["http://localhost:5174", "https://localhost", "http://localhost"]
)
def test_client_origin_allowed(client, origin):
    # Клиентское приложение: dev-сервер Vite и APK на Capacitor (https://localhost,
    # на стенде с сервисами по http — http://localhost).
    response = client.options(
        "/clips", headers={"Origin": origin, "Access-Control-Request-Method": "GET"}
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_foreign_origin_rejected(client):
    response = client.options(
        "/clips",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in response.headers
