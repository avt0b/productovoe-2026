from conftest import auth_header

from core.config import settings

INTERNAL_HEADERS = {"X-Internal-Key": settings.internal_api_key}

# Площадь Мира, Орёл — новая точка «Последнего боя».
POINT = {"lat": 52.9680, "lon": 36.0785}
# ~1 км от точки.
NEAR_HOME = {"home_lat": 52.9770, "home_lon": 36.0790}
# ~700 км от точки — Москва.
FAR_HOME = {"home_lat": 55.7558, "home_lon": 37.6173}


def subscribe(client, user_id, *, home, radius_km=20):
    header = auth_header(user_id=user_id)
    client.get("/profiles/me", headers=header)
    client.put(
        "/profiles/me",
        headers=header,
        json={"subscribed_to_search": True, "alert_radius_km": radius_km, **home},
    )
    return header


def broadcast(client, **over):
    body = {
        "title": "Рядом обнаружено место гибели бойца",
        "body": "Требуется помощь в идентификации.",
        **POINT,
    }
    body.update(over)
    return client.post(
        "/internal/notifications/broadcast-nearby", headers=INTERNAL_HEADERS, json=body
    )


def test_broadcast_notifies_only_nearby_subscribers(client):
    near_header = subscribe(client, "near-1", home=NEAR_HOME)
    subscribe(client, "far-1", home=FAR_HOME)

    r = broadcast(client)
    assert r.status_code == 200
    assert r.json()["notified"] == 1

    mine = client.get("/notifications", headers=near_header).json()
    assert len(mine) == 1
    assert mine[0]["kind"] == "last_stand_nearby"
    assert mine[0]["payload"]["distance_km"] < 5
    assert mine[0]["read_at"] is None

    far_mine = client.get("/notifications", headers=auth_header(user_id="far-1")).json()
    assert far_mine == []


def test_broadcast_substitutes_distance_placeholder(client):
    near_header = subscribe(client, "near-2", home=NEAR_HOME)

    r = broadcast(
        client,
        title="В {distance_km} км от вас обнаружено место гибели бойца",
        body="Требуется помощь в идентификации.",
    )
    assert r.json()["notified"] == 1

    mine = client.get("/notifications", headers=near_header).json()
    title = mine[0]["title"]
    assert "{distance_km}" not in title
    assert "км от вас обнаружено место гибели бойца" in title


def test_broadcast_ignores_unsubscribed_and_homeless_profiles(client):
    # Подписан, но без домашних координат — радиус не от чего считать.
    header = auth_header(user_id="no-home")
    client.get("/profiles/me", headers=header)
    client.put("/profiles/me", headers=header, json={"subscribed_to_search": True})

    # Есть домашние координаты рядом, но подписки нет.
    subscribe(client, "not-subscribed", home=NEAR_HOME)
    client.put(
        "/profiles/me",
        headers=auth_header(user_id="not-subscribed"),
        json={"subscribed_to_search": False},
    )

    assert broadcast(client).json()["notified"] == 0


def test_broadcast_respects_each_users_own_radius(client):
    # Дом рядом, но радиус слишком мал.
    header = subscribe(client, "tight-radius", home=NEAR_HOME, radius_km=1)
    assert broadcast(client).json()["notified"] == 0
    assert client.get("/notifications", headers=header).json() == []


def test_mark_read_only_by_owner(client):
    owner_header = subscribe(client, "owner-1", home=NEAR_HOME)
    broadcast(client)
    notification_id = client.get("/notifications", headers=owner_header).json()[0]["id"]

    stranger = auth_header(user_id="stranger")
    assert (
        client.post(f"/notifications/{notification_id}/read", headers=stranger).status_code == 403
    )

    marked = client.post(f"/notifications/{notification_id}/read", headers=owner_header)
    assert marked.status_code == 200
    assert marked.json()["read_at"] is not None

    unread = client.get("/notifications", headers=owner_header, params={"unread_only": True}).json()
    assert unread == []


def test_device_registration_upserts_by_token(client):
    header = auth_header(user_id="dev-1")
    r1 = client.post(
        "/notifications/devices", headers=header, json={"platform": "android", "token": "tok-1"}
    )
    assert r1.status_code == 201

    other_user_header = auth_header(user_id="dev-2")
    r2 = client.post(
        "/notifications/devices",
        headers=other_user_header,
        json={"platform": "ios", "token": "tok-1"},
    )
    assert r2.status_code == 201
    assert r2.json()["id"] == r1.json()["id"]
    assert r2.json()["platform"] == "ios"


def test_unregister_device(client):
    header = auth_header(user_id="dev-3")
    client.post(
        "/notifications/devices", headers=header, json={"platform": "web", "token": "tok-3"}
    )
    assert client.delete("/notifications/devices/tok-3", headers=header).status_code == 204
    assert client.delete("/notifications/devices/tok-3", headers=header).status_code == 404
