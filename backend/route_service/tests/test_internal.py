from conftest import auth_header

from core.config import settings

INTERNAL_HEADER = {"X-Internal-Key": settings.internal_api_key}


def make_route(client, header, **over):
    body = {"title": "Тропа памяти: Орёл", "mode": "family", "city": "Орёл", "distance_km": 3}
    body.update(over)
    return client.post("/routes", headers=header, json=body)


def add_wp(client, header, route_id, **over):
    body = {
        "title": "Оборона 41-го полка",
        "lat": 52.9686,
        "lon": 36.0694,
        "story": "Здесь держал оборону 41-й полк.",
        "kid_task": "Найди калибр пушки на иллюстрации",
    }
    body.update(over)
    return client.post(f"/routes/{route_id}/waypoints", headers=header, json=body)


# --- проверка ключа ---


def test_stats_requires_internal_key(client):
    assert client.get("/internal/stats").status_code == 403


def test_stats_rejects_wrong_key(client):
    r = client.get("/internal/stats", headers={"X-Internal-Key": "wrong-key"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Недействительный внутренний ключ"


def test_list_routes_requires_internal_key(client):
    assert client.get("/internal/routes").status_code == 403


def test_publish_requires_internal_key(client, author_header):
    route = make_route(client, author_header).json()
    r = client.post(f"/internal/routes/{route['id']}/publish", json={"is_published": True})
    assert r.status_code == 403


def test_delete_requires_internal_key(client, author_header):
    route = make_route(client, author_header).json()
    r = client.delete(f"/internal/routes/{route['id']}")
    assert r.status_code == 403


# --- /internal/stats ---


def test_stats_shape(client, author_header):
    draft = make_route(client, author_header, title="Черновик").json()
    published = make_route(client, author_header, title="Опубликован", mode="general").json()
    add_wp(client, author_header, published["id"])
    client.post(
        f"/routes/{published['id']}/publish", headers=author_header, json={"is_published": True}
    )

    family = auth_header(user_id="family-1", role="family")
    client.post(f"/routes/{published['id']}/progress/start", headers=family)

    r = client.get("/internal/stats", headers=INTERNAL_HEADER)
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "route_service"
    assert data["routes_total"] == 2
    assert data["published"] == 1
    assert data["drafts"] == 1
    assert data["by_mode"]["family"] == 1
    assert data["by_mode"]["general"] == 1
    assert data["waypoints_total"] == 1
    assert data["progress_started"] == 1
    assert data["progress_completed"] == 0
    assert data["completion_rate"] == 0.0
    assert data["started_7d"] == 1
    assert draft["id"]  # черновик тоже создан, но не опубликован


def test_stats_completion_rate(client, author_header):
    route = make_route(client, author_header).json()
    wp = add_wp(client, author_header, route["id"]).json()
    client.post(
        f"/routes/{route['id']}/publish", headers=author_header, json={"is_published": True}
    )

    family = auth_header(user_id="family-1", role="family")
    client.post(
        f"/routes/{route['id']}/progress/complete-waypoint",
        headers=family,
        json={"waypoint_id": wp["id"]},
    )

    r = client.get("/internal/stats", headers=INTERNAL_HEADER)
    data = r.json()
    assert data["progress_started"] == 1
    assert data["progress_completed"] == 1
    assert data["completion_rate"] == 1.0


# --- /internal/routes ---


def test_list_routes_sees_drafts(client, author_header):
    draft = make_route(client, author_header).json()

    r = client.get("/internal/routes", headers=INTERNAL_HEADER)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["limit"] == 50
    assert data["offset"] == 0
    assert [item["id"] for item in data["items"]] == [draft["id"]]
    assert data["items"][0]["is_published"] is False


def test_list_routes_filters_by_published_mode_and_query(client, author_header):
    draft = make_route(client, author_header, title="Черновик", city="Мценск").json()
    published = make_route(
        client, author_header, title="Готовый маршрут", mode="general", city="Орёл"
    ).json()
    add_wp(client, author_header, published["id"])
    client.post(
        f"/routes/{published['id']}/publish", headers=author_header, json={"is_published": True}
    )

    r = client.get("/internal/routes", headers=INTERNAL_HEADER, params={"is_published": "true"})
    assert [x["id"] for x in r.json()["items"]] == [published["id"]]

    r = client.get("/internal/routes", headers=INTERNAL_HEADER, params={"is_published": "false"})
    assert [x["id"] for x in r.json()["items"]] == [draft["id"]]

    r = client.get("/internal/routes", headers=INTERNAL_HEADER, params={"mode": "general"})
    assert [x["id"] for x in r.json()["items"]] == [published["id"]]

    r = client.get("/internal/routes", headers=INTERNAL_HEADER, params={"query": "Мценск"})
    assert [x["id"] for x in r.json()["items"]] == [draft["id"]]


# --- мутации через internal_actor ---


def test_internal_publish_bypasses_ownership(client, author_header):
    route = make_route(client, author_header).json()
    add_wp(client, author_header, route["id"])

    r = client.post(
        f"/internal/routes/{route['id']}/publish",
        headers={**INTERNAL_HEADER, "X-Actor-Id": "admin-1"},
        json={"is_published": True},
    )
    assert r.status_code == 200
    assert r.json()["is_published"] is True

    # виден теперь и в публичной ленте
    assert route["id"] in [x["id"] for x in client.get("/routes").json()]


def test_internal_publish_without_waypoints_is_409(client, author_header):
    route = make_route(client, author_header).json()

    r = client.post(
        f"/internal/routes/{route['id']}/publish",
        headers=INTERNAL_HEADER,
        json={"is_published": True},
    )
    assert r.status_code == 409


def test_internal_unpublish(client, author_header):
    route = make_route(client, author_header).json()
    add_wp(client, author_header, route["id"])
    client.post(
        f"/routes/{route['id']}/publish", headers=author_header, json={"is_published": True}
    )

    r = client.post(
        f"/internal/routes/{route['id']}/publish",
        headers=INTERNAL_HEADER,
        json={"is_published": False},
    )
    assert r.status_code == 200
    assert r.json()["is_published"] is False
    assert client.get("/routes").json() == []


def test_internal_delete_bypasses_ownership(client, author_header):
    route = make_route(client, author_header).json()

    r = client.delete(
        f"/internal/routes/{route['id']}",
        headers={**INTERNAL_HEADER, "X-Actor-Id": "admin-1"},
    )
    assert r.status_code == 204
    assert client.get(f"/routes/{route['id']}", headers=author_header).status_code == 404


def test_internal_publish_missing_route_404(client):
    r = client.post(
        "/internal/routes/does-not-exist/publish",
        headers=INTERNAL_HEADER,
        json={"is_published": True},
    )
    assert r.status_code == 404
