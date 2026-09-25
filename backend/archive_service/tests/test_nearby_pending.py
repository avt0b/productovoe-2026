from conftest import auth_header

# Площадь Мира, Орёл.
NEAR = {"lat": 52.9680, "lon": 36.0785}
# Другой регион — заведомо вне bbox ниже.
FAR = {"lat": 55.7558, "lon": 37.6173}
BBOX = {"min_lat": 52.95, "min_lon": 36.06, "max_lat": 52.98, "max_lon": 36.09}
CIRCLE = {**NEAR, "radius_km": 10}
# Угол рамки 10 км: по диагонали до него ~14 км — в круг он попасть не должен.
CORNER = {"lat": NEAR["lat"] + 10 / 111, "lon": NEAR["lon"] + 10 / (111 * 0.6027)}
# В полутора километрах к северу — ближе угла, но дальше самой точки.
CLOSE = {"lat": NEAR["lat"] + 1.5 / 111, "lon": NEAR["lon"]}


def create_entry(client, header, **over):
    body = {
        "kind": "event",
        "title": "Окоп у площади Мира",
        "body": "Рассказ местного жителя.",
        **NEAR,
    }
    body.update(over)
    return client.post("/entries", headers=header, json=body)


def test_nearby_pending_returns_unverified_entry_in_bbox(client):
    entry = create_entry(client, auth_header(user_id="author-1")).json()

    r = client.get("/entries/nearby-pending", params=BBOX)
    assert r.status_code == 200
    body = r.json()
    assert [e["id"] for e in body] == [entry["id"]]
    # Витрина куцая: без body и submitted_by.
    assert "body" not in body[0]
    assert "submitted_by" not in body[0]
    assert body[0]["title"] == "Окоп у площади Мира"


def test_nearby_pending_ignores_verified_and_out_of_bbox(client):
    verified = create_entry(client, auth_header(user_id="author-1"), title="Уже проверено").json()
    client.post(
        f"/entries/{verified['id']}/verify", headers=auth_header(role="local_historian"), json={}
    )
    create_entry(client, auth_header(user_id="author-2"), title="Далеко", **FAR)

    assert client.get("/entries/nearby-pending", params=BBOX).json() == []


def test_nearby_pending_requires_no_auth(client):
    create_entry(client, auth_header())
    r = client.get("/entries/nearby-pending", params=BBOX)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_nearby_pending_by_radius_returns_only_circle(client):
    inside = create_entry(client, auth_header(user_id="author-1"), title="В круге").json()
    create_entry(client, auth_header(user_id="author-2"), title="В углу рамки", **CORNER)

    r = client.get("/entries/nearby-pending", params=CIRCLE)
    assert r.status_code == 200
    # Угол рамки в круг не попал — ради этого радиус и заводили.
    assert [e["id"] for e in r.json()] == [inside["id"]]


def test_nearby_pending_by_radius_sorted_by_distance(client):
    far = create_entry(client, auth_header(user_id="author-1"), title="Подальше", **CLOSE).json()
    near = create_entry(client, auth_header(user_id="author-2"), title="Под боком").json()

    body = client.get("/entries/nearby-pending", params=CIRCLE).json()
    assert [e["id"] for e in body] == [near["id"], far["id"]]


def test_nearby_pending_by_radius_ignores_verified(client):
    verified = create_entry(client, auth_header(user_id="author-1"), title="Уже проверено").json()
    client.post(
        f"/entries/{verified['id']}/verify", headers=auth_header(role="local_historian"), json={}
    )

    assert client.get("/entries/nearby-pending", params=CIRCLE).json() == []


def test_nearby_pending_without_circle_and_bbox_is_422(client):
    create_entry(client, auth_header())
    assert client.get("/entries/nearby-pending").status_code == 422
    # Половина круга — тоже не круг.
    assert client.get("/entries/nearby-pending", params=NEAR).status_code == 422
