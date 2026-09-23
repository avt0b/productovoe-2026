import uuid

from conftest import auth_header

# Орёл и окрестности
OREL = {"lat": 52.9686, "lon": 36.0694}
KRUPYSHINO = {"lat": 52.74, "lon": 35.97}


def make_poi(client, header, **over):
    body = {
        "kind": "monument",
        "title": "Памятник морякам ТОФ",
        "description": "с. Крупышино, Кромской район",
        "lat": KRUPYSHINO["lat"],
        "lon": KRUPYSHINO["lon"],
        "date_text": "1943",
        "source": "Книга Памяти, Т. 5",
    }
    body.update(over)
    return client.post("/poi", headers=header, json=body)


def test_create_requires_auth(client):
    assert make_poi(client, {}).status_code in (401, 403)


def test_create_and_get(client):
    h = auth_header(role="local_historian")
    r = make_poi(client, h)
    assert r.status_code == 201
    poi = r.json()
    assert poi["kind"] == "monument"
    assert poi["created_by"]

    got = client.get(f"/poi/{poi['id']}")
    assert got.status_code == 200
    assert got.json()["title"] == "Памятник морякам ТОФ"


def test_list_filters_by_kind_and_bbox(client):
    h = auth_header(role="local_historian")
    make_poi(client, h, kind="grave", title="Братская могила", lat=OREL["lat"], lon=OREL["lon"])
    make_poi(client, h, kind="monument", title="Обелиск", lat=55.75, lon=37.62)  # Москва

    graves = client.get("/poi", params={"kind": "grave"}).json()
    assert len(graves) == 1 and graves[0]["kind"] == "grave"

    near_orel = client.get(
        "/poi",
        params={"min_lat": 52, "min_lon": 35, "max_lat": 53.5, "max_lon": 37},
    ).json()
    titles = {p["title"] for p in near_orel}
    assert "Братская могила" in titles and "Обелиск" not in titles


def test_nearby_returns_distance_sorted(client):
    h = auth_header(role="local_historian")
    make_poi(client, h, title="A", lat=52.97, lon=36.07)
    make_poi(client, h, title="B", lat=53.30, lon=36.50)

    res = client.get("/poi/nearby", params={**OREL, "radius_km": 10}).json()
    assert [p["title"] for p in res] == ["A"]
    assert res[0]["distance_km"] >= 0

    res_wide = client.get("/poi/nearby", params={**OREL, "radius_km": 100}).json()
    assert [p["title"] for p in res_wide] == ["A", "B"]
    assert res_wide[0]["distance_km"] <= res_wide[1]["distance_km"]


def test_only_author_or_moderator_edits(client):
    owner = auth_header(role="local_historian")
    poi = make_poi(client, owner).json()

    stranger = auth_header(role="local_historian")
    assert (
        client.patch(f"/poi/{poi['id']}", headers=stranger, json={"title": "hack"}).status_code
        == 403
    )

    assert (
        client.patch(f"/poi/{poi['id']}", headers=owner, json={"title": "fixed"}).status_code == 200
    )
    mod = auth_header(role="moderator")
    assert (
        client.patch(
            f"/poi/{poi['id']}", headers=mod, json={"description": "проверено"}
        ).status_code
        == 200
    )


def test_delete_by_root(client):
    poi = make_poi(client, auth_header(role="local_historian")).json()
    assert client.delete(f"/poi/{poi['id']}", headers=auth_header(is_root=True)).status_code == 204
    assert client.get(f"/poi/{poi['id']}").status_code == 404


def test_bad_coordinates_rejected(client):
    assert make_poi(client, auth_header(role="local_historian"), lat=200).status_code == 422


def test_create_requires_contributor_role(client):
    r = make_poi(client, auth_header(role="family"))
    assert r.status_code == 403


def test_get_missing_404(client):
    assert client.get(f"/poi/{uuid.uuid4()}").status_code == 404
