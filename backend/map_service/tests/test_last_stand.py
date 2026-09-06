from conftest import auth_header

KRUPYSHINO = {"lat": 52.74, "lon": 35.97}


def make_point(client, header, **over):
    body = {
        "soldier_name": "Красноармеец Иванов И.И.",
        "unit": "9-я воздушно-десантная бригада",
        "lat": KRUPYSHINO["lat"],
        "lon": KRUPYSHINO["lon"],
        "circumstances": "Овраг у д. Крупышино, октябрь 1941",
        "date_text": "октябрь 1941",
        "source": "Книга Памяти, Т. 5",
    }
    body.update(over)
    return client.post("/last-stand", headers=header, json=body)


def test_contributor_roles_only(client):
    assert make_point(client, auth_header(role="family")).status_code == 403
    assert make_point(client, auth_header(role="searcher")).status_code == 201
    assert make_point(client, auth_header(role="local_historian")).status_code == 201


def test_default_status_is_discovered(client):
    r = make_point(client, auth_header(role="searcher"))
    assert r.json()["status"] == "discovered"


def test_status_change_moderator_only(client):
    point = make_point(client, auth_header(role="searcher")).json()

    assert client.patch(
        f"/last-stand/{point['id']}/status",
        headers=auth_header(role="searcher"),
        json={"status": "archive_confirmed"},
    ).status_code == 403

    r = client.patch(
        f"/last-stand/{point['id']}/status",
        headers=auth_header(role="moderator"),
        json={"status": "remains_raised"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "remains_raised"


def test_list_filter_by_status(client):
    p1 = make_point(client, auth_header(role="searcher")).json()
    make_point(client, auth_header(role="searcher"))
    client.patch(
        f"/last-stand/{p1['id']}/status",
        headers=auth_header(role="moderator"),
        json={"status": "archive_confirmed"},
    )
    confirmed = client.get("/last-stand", params={"status": "archive_confirmed"}).json()
    assert len(confirmed) == 1 and confirmed[0]["id"] == p1["id"]


def test_nearby_alert_radius(client):
    make_point(client, auth_header(role="searcher"), lat=52.74, lon=35.97)
    # волонтёр в ~5 км
    res = client.get("/last-stand/nearby", params={"lat": 52.78, "lon": 35.99, "radius_km": 20})
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["distance_km"] < 20

    far = client.get("/last-stand/nearby", params={"lat": 55.75, "lon": 37.62, "radius_km": 20})
    assert far.json() == []


def test_anonymous_can_read(client):
    make_point(client, auth_header(role="searcher"))
    assert client.get("/last-stand").status_code == 200
