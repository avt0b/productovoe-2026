import pytest
from conftest import auth_header

import services.route_service as route_service_module

CENTER = {"lat": 52.9686, "lon": 36.0694}


@pytest.fixture()
def fake_poi(monkeypatch):
    """Подменяет поход в map_service: тест сам решает, что «найдено» рядом."""
    calls = []

    async def fake_fetch(*, lat, lon, radius_km, kind=None, limit=50):
        calls.append({"lat": lat, "lon": lon, "radius_km": radius_km, "kind": kind})
        return fake_fetch.result

    fake_fetch.result = []
    monkeypatch.setattr(route_service_module, "fetch_poi_nearby", fake_fetch)
    fake_fetch.calls = calls
    return fake_fetch


def poi(id_, lat, lon, title="Точка", description="Описание"):
    return {"id": id_, "lat": lat, "lon": lon, "title": title, "description": description}


def auto_generate(client, header, **over):
    body = {**CENTER, "radius_km": 3}
    body.update(over)
    return client.post("/routes/auto-generate", headers=header, json=body)


def test_requires_author_role(client, fake_poi):
    fake_poi.result = [poi("p1", CENTER["lat"], CENTER["lon"])]
    r = auto_generate(client, auth_header(role="family"))
    assert r.status_code == 403


def test_no_points_nearby_is_conflict(client, fake_poi):
    fake_poi.result = []
    r = auto_generate(client, auth_header(role="local_historian"))
    assert r.status_code == 409


def test_builds_draft_route_ordered_and_capped(client, fake_poi):
    # p1 ближе к центру, p2 дальше — но p3 ближе к p2, чем к центру:
    # жадный обход должен пойти центр -> p1 -> p2 -> p3, а не по радиальной дистанции от центра.
    fake_poi.result = [
        poi("p2", CENTER["lat"] + 0.02, CENTER["lon"], title="Дальняя"),
        poi("p1", CENTER["lat"] + 0.001, CENTER["lon"], title="Ближняя"),
        poi("p3", CENTER["lat"] + 0.021, CENTER["lon"], title="Рядом с дальней"),
    ]

    r = auto_generate(
        client, auth_header(role="local_historian"), max_points=2, title=None, city="Орёл"
    )
    assert r.status_code == 201
    body = r.json()
    assert body["is_published"] is False
    assert body["city"] == "Орёл"
    assert body["title"] == "Маршрут по «Орёл»"
    assert len(body["waypoints"]) == 2
    assert [w["title"] for w in body["waypoints"]] == ["Ближняя", "Дальняя"]
    assert body["waypoints"][0]["poi_id"] == "p1"
    assert body["waypoints"][0]["order_index"] == 0
    assert body["waypoints"][1]["order_index"] == 1
    assert body["distance_km"] > 0

    # черновик виден автору, но не публике.
    assert client.get(f"/routes/{body['id']}").status_code == 404
    assert client.get(f"/routes/{body['id']}", headers=auth_header(role="local_historian", user_id="stranger")).status_code == 404


def test_kind_filter_passed_through(client, fake_poi):
    fake_poi.result = [poi("p1", CENTER["lat"], CENTER["lon"])]
    auto_generate(client, auth_header(role="local_historian"), kind="grave")
    assert fake_poi.calls[-1]["kind"] == "grave"
