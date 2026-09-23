import pytest

import services.archive_prompt_service as archive_prompt_service_module

WAYPOINT_A = {"lat": 52.9686, "lon": 36.0694}
WAYPOINT_B = {"lat": 52.9540, "lon": 36.0627}


def make_route(client, header, **over):
    body = {"title": "Тропа памяти: Орёл", "mode": "family", "city": "Орёл", "distance_km": 3}
    body.update(over)
    return client.post("/routes", headers=header, json=body).json()


def add_wp(client, header, route_id, **over):
    body = {
        "title": "Точка",
        "story": "",
        "kid_task": "",
        **WAYPOINT_A,
    }
    body.update(over)
    return client.post(f"/routes/{route_id}/waypoints", headers=header, json=body).json()


def publish(client, header, route_id):
    client.post(f"/routes/{route_id}/publish", headers=header, json={"is_published": True})


@pytest.fixture()
def fake_entries(monkeypatch):
    """Подменяет поход в archive_service: тест сам решает, что «найдено» рядом."""
    calls = []

    async def fake_fetch(bbox, *, limit=100):
        calls.append(bbox)
        return fake_fetch.result

    fake_fetch.result = []
    monkeypatch.setattr(archive_prompt_service_module, "fetch_nearby_pending", fake_fetch)
    fake_fetch.calls = calls
    return fake_fetch


def test_prompt_matches_nearest_waypoint(client, author_header, fake_entries):
    route = make_route(client, author_header)
    wp_a = add_wp(client, author_header, route["id"], title="У площади Мира", **WAYPOINT_A)
    add_wp(client, author_header, route["id"], title="Музей", **WAYPOINT_B)
    publish(client, author_header, route["id"])

    fake_entries.result = [
        {
            "id": "entry-1",
            "kind": "memory",
            "title": "Рассказ местного жителя",
            "lat": WAYPOINT_A["lat"] + 0.0005,
            "lon": WAYPOINT_A["lon"] + 0.0005,
            "created_at": "2026-01-01T00:00:00",
        }
    ]

    r = client.get(f"/routes/{route['id']}/archive-prompts")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["waypoint_id"] == wp_a["id"]
    assert body[0]["entry_id"] == "entry-1"
    assert body[0]["distance_km"] < 0.2


def test_prompt_dropped_when_too_far_from_every_waypoint(client, author_header, fake_entries):
    route = make_route(client, author_header)
    add_wp(client, author_header, route["id"], **WAYPOINT_A)
    publish(client, author_header, route["id"])

    fake_entries.result = [
        {
            "id": "entry-far",
            "kind": "event",
            "title": "Далёкая заметка",
            # ~15 км от точки маршрута — за пределами радиуса по умолчанию (2 км).
            "lat": WAYPOINT_A["lat"] + 0.15,
            "lon": WAYPOINT_A["lon"],
            "created_at": "2026-01-01T00:00:00",
        }
    ]

    assert client.get(f"/routes/{route['id']}/archive-prompts").json() == []


def test_entries_without_coords_are_skipped(client, author_header, fake_entries):
    route = make_route(client, author_header)
    add_wp(client, author_header, route["id"], **WAYPOINT_A)
    publish(client, author_header, route["id"])

    fake_entries.result = [
        {
            "id": "no-geo",
            "kind": "soldier_card",
            "title": "Карточка",
            "lat": None,
            "lon": None,
            "created_at": "2026-01-01T00:00:00",
        }
    ]

    assert client.get(f"/routes/{route['id']}/archive-prompts").json() == []


def test_route_without_waypoints_skips_archive_call(client, author_header, fake_entries):
    route = make_route(client, author_header)
    r = client.get(f"/routes/{route['id']}/archive-prompts", headers=author_header)
    assert r.status_code == 200
    assert r.json() == []
    assert fake_entries.calls == []


def test_draft_route_prompts_hidden_from_strangers(client, author_header, fake_entries):
    route = make_route(client, author_header)
    add_wp(client, author_header, route["id"], **WAYPOINT_A)
    # не публикуем

    assert client.get(f"/routes/{route['id']}/archive-prompts").status_code == 404
    assert (
        client.get(f"/routes/{route['id']}/archive-prompts", headers=author_header).status_code
        == 200
    )
