from conftest import auth_header

from core.config import settings
from core.models import Notification
from services import fcm_client, push_service

INTERNAL_HEADERS = {"X-Internal-Key": settings.internal_api_key}


def register_device(client, user_id, token, platform="android"):
    return client.post(
        "/notifications/devices",
        headers=auth_header(user_id=user_id),
        json={"platform": platform, "token": token},
    )


def test_deliver_does_nothing_when_fcm_not_configured(client, monkeypatch, db_session):
    monkeypatch.setattr(fcm_client, "is_configured", lambda: False)
    calls = []
    monkeypatch.setattr(fcm_client, "send", lambda **kw: calls.append(kw))

    register_device(client, "u1", "tok-1")
    notification = Notification(user_id="u1", kind="test", title="t", body="b")
    db_session.add(notification)
    db_session.flush()

    push_service.deliver(db_session, notification)
    assert calls == []


def test_deliver_sends_to_every_registered_device(client, monkeypatch, db_session):
    monkeypatch.setattr(fcm_client, "is_configured", lambda: True)
    calls = []

    def fake_send(**kw):
        calls.append(kw)
        return fcm_client.SendResult.ok

    monkeypatch.setattr(fcm_client, "send", fake_send)

    register_device(client, "u1", "tok-android", platform="android")
    register_device(client, "u1", "tok-ios", platform="ios")
    register_device(client, "u2", "tok-other")  # чужое устройство — не должно попасть в выборку

    notification = Notification(
        user_id="u1", kind="achievement", title="Новое достижение!", body="Жертвователь"
    )
    db_session.add(notification)
    db_session.flush()

    push_service.deliver(db_session, notification)

    assert len(calls) == 2
    tokens = {c["token"] for c in calls}
    assert tokens == {"tok-android", "tok-ios"}
    for c in calls:
        assert c["title"] == "Новое достижение!"
        assert c["body"] == "Жертвователь"
        assert c["data"] == {"kind": "achievement", "notification_id": notification.id}


def test_deliver_removes_device_with_invalid_token(client, monkeypatch, db_session):
    monkeypatch.setattr(fcm_client, "is_configured", lambda: True)
    monkeypatch.setattr(fcm_client, "send", lambda **kw: fcm_client.SendResult.token_invalid)

    register_device(client, "u1", "dead-token")
    notification = Notification(user_id="u1", kind="test", title="t", body="b")
    db_session.add(notification)
    db_session.flush()

    push_service.deliver(db_session, notification)

    devices = client.post(
        "/notifications/devices",
        headers=auth_header(user_id="u1"),
        json={"platform": "android", "token": "dead-token"},
    ).json()
    # повторная регистрация создала запись заново — значит старая была удалена,
    # а не просто "не найдена" (иначе id совпал бы с апдейтом того же токена
    # без ошибок, что не отличило бы удаление от отсутствия эффекта).
    assert devices["token"] == "dead-token"


def test_broadcast_nearby_triggers_push_for_matched_subscribers(client, monkeypatch):
    monkeypatch.setattr(fcm_client, "is_configured", lambda: True)
    calls = []

    def fake_send(**kw):
        calls.append(kw)
        return fcm_client.SendResult.ok

    monkeypatch.setattr(fcm_client, "send", fake_send)

    header = auth_header(user_id="near-1")
    client.get("/profiles/me", headers=header)
    client.put(
        "/profiles/me",
        headers=header,
        json={"subscribed_to_search": True, "alert_radius_km": 20, "home_lat": 52.977, "home_lon": 36.079},
    )
    register_device(client, "near-1", "push-tok")

    r = client.post(
        "/internal/notifications/broadcast-nearby",
        headers=INTERNAL_HEADERS,
        json={"lat": 52.968, "lon": 36.0785, "title": "В {distance_km} км от вас", "body": "Тест"},
    )
    assert r.json()["notified"] == 1
    assert len(calls) == 1
    assert calls[0]["token"] == "push-tok"
    assert "{distance_km}" not in calls[0]["title"]


def test_award_achievement_triggers_push(client, monkeypatch):
    monkeypatch.setattr(fcm_client, "is_configured", lambda: True)
    calls = []

    def fake_send(**kw):
        calls.append(kw)
        return fcm_client.SendResult.ok

    monkeypatch.setattr(fcm_client, "send", fake_send)

    register_device(client, "u1", "push-tok")
    r = client.post(
        "/internal/achievements/award",
        headers=INTERNAL_HEADERS,
        json={"user_id": "u1", "code": "donor"},
    )
    assert r.status_code == 200
    assert len(calls) == 1
    assert calls[0]["token"] == "push-tok"
    assert calls[0]["body"] == "Жертвователь"
