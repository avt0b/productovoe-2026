import pytest
from conftest import auth_header

import services.last_stand_service as last_stand_service_module

KRUPYSHINO = {"lat": 52.74, "lon": 35.97}


@pytest.fixture()
def notify_spy(monkeypatch):
    calls = []
    monkeypatch.setattr(
        last_stand_service_module,
        "notify_nearby_subscribers",
        lambda **kw: calls.append(kw),
    )
    return calls


def make_point(client, header, **over):
    body = {
        "soldier_name": "Красноармеец Иванов И.И.",
        "unit": "9-я воздушно-десантная бригада",
        "circumstances": "Овраг у д. Крупышино, октябрь 1941",
        **KRUPYSHINO,
    }
    body.update(over)
    return client.post("/last-stand", headers=header, json=body)


def test_creating_point_notifies_nearby_subscribers(client, notify_spy):
    r = make_point(client, auth_header(role="searcher"))
    assert r.status_code == 201

    assert len(notify_spy) == 1
    call = notify_spy[0]
    assert call["lat"] == KRUPYSHINO["lat"]
    assert call["lon"] == KRUPYSHINO["lon"]
    assert "Иванов" in call["title"]


def test_unknown_soldier_gets_generic_title(client, notify_spy):
    make_point(client, auth_header(role="searcher"), soldier_name="")
    assert "обнаружено место гибели бойца" in notify_spy[0]["title"]


def test_creating_point_increments_finds_stat(client, monkeypatch):
    calls = []
    monkeypatch.setattr(
        last_stand_service_module, "increment_stat", lambda **kw: calls.append(kw)
    )

    make_point(client, auth_header(role="searcher", user_id="searcher-1"))

    assert calls == [{"user_id": "searcher-1", "metric": "finds_count"}]


def test_user_service_outage_does_not_break_point_creation(client, monkeypatch):
    """Без autouse-подмены: реальный notify_client бьётся в недоступный порт и сам
    гасит httpx.HTTPError — создание точки не должно от этого падать."""
    from core.config import settings
    from services.notify_client import notify_nearby_subscribers

    monkeypatch.setattr(
        last_stand_service_module, "notify_nearby_subscribers", notify_nearby_subscribers
    )
    monkeypatch.setattr(settings, "user_service_url", "http://127.0.0.1:1")
    monkeypatch.setattr(settings, "upstream_timeout_seconds", 0.5)

    r = make_point(client, auth_header(role="searcher"))
    assert r.status_code == 201
