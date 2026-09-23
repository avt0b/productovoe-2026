from core.db import SessionLocal
from scripts.seed_orel import LAST_STAND, POI, SEED_AUTHOR, seed, seed_id


def test_seed_is_idempotent(client):
    with SessionLocal() as db:
        first = seed(db)
        second = seed(db)

    assert first == second == {"poi": len(POI), "last_stand": len(LAST_STAND)}
    assert len(client.get("/poi", params={"limit": 500}).json()) == len(POI)
    assert len(client.get("/last-stand", params={"limit": 500}).json()) == len(LAST_STAND)


def test_seed_is_public_and_covers_every_status(client):
    with SessionLocal() as db:
        seed(db)

    points = client.get("/last-stand").json()
    assert {p["status"] for p in points} == {"discovered", "archive_confirmed", "remains_raised"}
    assert all(p["created_by"] == SEED_AUTHOR for p in points)
    # Демо «Последнего боя» не должно выглядеть архивной записью.
    assert all(p["source"].startswith("ДЕМО") for p in points)

    grave = client.get(f"/poi/{seed_id('poi', 'orel-mass-grave')}")
    assert grave.status_code == 200
    assert grave.json()["kind"] == "grave"


def test_seed_points_are_found_nearby(client):
    with SessionLocal() as db:
        seed(db)

    # Площадь Мира: в радиусе километра — братская могила, Вечный огонь, танк, памятник освободителям.
    nearby = client.get(
        "/poi/nearby", params={"lat": 52.96822, "lon": 36.07936, "radius_km": 1}
    ).json()
    ids = {p["id"] for p in nearby}
    for key in ("orel-mass-grave", "orel-eternal-flame", "orel-t34", "orel-liberators"):
        assert seed_id("poi", key) in ids


def test_client_origin_is_allowed_by_cors(client):
    for origin in ("http://localhost:5174", "https://localhost"):
        response = client.options(
            "/poi", headers={"Origin": origin, "Access-Control-Request-Method": "GET"}
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin

    foreign = client.options(
        "/poi", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"}
    )
    assert "access-control-allow-origin" not in foreign.headers
