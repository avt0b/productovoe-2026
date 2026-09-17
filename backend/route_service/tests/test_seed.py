import uuid

from core.db import SessionLocal
from scripts.seed_orel import ROUTE_KEY, WAYPOINTS, seed, seed_id


def test_seed_is_idempotent_and_published(client):
    with SessionLocal() as db:
        first = seed(db)
        second = seed(db)

    assert first == second == {"routes": 1, "waypoints": len(WAYPOINTS)}

    routes = client.get("/routes", params={"mode": "family"}).json()
    assert [r["id"] for r in routes] == [seed_id("route", ROUTE_KEY)]


def test_seed_route_has_ordered_waypoints(client):
    with SessionLocal() as db:
        seed(db)

    detail = client.get(f"/routes/{seed_id('route', ROUTE_KEY)}").json()
    waypoints = detail["waypoints"]
    assert [w["order_index"] for w in waypoints] == list(range(len(WAYPOINTS)))
    assert [w["title"] for w in waypoints] == [w.title for w in WAYPOINTS]
    assert all(w["kid_task"] for w in waypoints)


def test_waypoints_link_to_map_service_poi_ids():
    # Неймспейс обязан совпадать с map_service/scripts/seed_orel.py — иначе poi_id
    # точек маршрута будут указывать в пустоту.
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, "marshruty/seed/orel")
    expected = str(uuid.uuid5(namespace, "poi:orel-t34"))
    assert seed_id("poi", "orel-t34") == expected


def test_client_origin_is_allowed_by_cors(client):
    response = client.options(
        "/routes",
        headers={"Origin": "https://localhost", "Access-Control-Request-Method": "GET"},
    )
    assert response.headers["access-control-allow-origin"] == "https://localhost"
