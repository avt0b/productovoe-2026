from conftest import auth_header

# Площадь Мира, Орёл.
NEAR = {"lat": 52.9680, "lon": 36.0785}
# Другой регион — заведомо вне bbox ниже.
FAR = {"lat": 55.7558, "lon": 37.6173}
BBOX = {"min_lat": 52.95, "min_lon": 36.06, "max_lat": 52.98, "max_lon": 36.09}


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
