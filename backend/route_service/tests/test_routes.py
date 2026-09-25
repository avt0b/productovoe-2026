import uuid

from conftest import auth_header


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


def test_only_curator_creates_route(client):
    assert make_route(client, auth_header(role="family")).status_code == 403
    assert make_route(client, auth_header(role="local_historian")).status_code == 201


def test_draft_hidden_from_public_until_published(client, author_header):
    route = make_route(client, author_header).json()
    assert route["is_published"] is False
    assert client.get("/routes").json() == []
    # аноним не видит черновик
    assert client.get(f"/routes/{route['id']}").status_code == 404
    # автор видит
    assert client.get(f"/routes/{route['id']}", headers=author_header).status_code == 200


def test_cannot_publish_without_waypoints(client, author_header):
    route = make_route(client, author_header).json()
    r = client.post(
        f"/routes/{route['id']}/publish", headers=author_header, json={"is_published": True}
    )
    assert r.status_code == 409

    add_wp(client, author_header, route["id"])
    r2 = client.post(
        f"/routes/{route['id']}/publish", headers=author_header, json={"is_published": True}
    )
    assert r2.status_code == 200
    assert r2.json()["is_published"] is True
    assert len(client.get("/routes").json()) == 1


def test_waypoint_order_autoincrement_and_reorder(client, author_header):
    route = make_route(client, author_header).json()
    w1 = add_wp(client, author_header, route["id"], title="A").json()
    w2 = add_wp(client, author_header, route["id"], title="B").json()
    w3 = add_wp(client, author_header, route["id"], title="C").json()
    assert [w1["order_index"], w2["order_index"], w3["order_index"]] == [0, 1, 2]

    reordered = client.post(
        f"/routes/{route['id']}/waypoints/reorder",
        headers=author_header,
        json={"ordered_ids": [w3["id"], w1["id"], w2["id"]]},
    ).json()
    assert [w["title"] for w in reordered] == ["C", "A", "B"]


def test_reorder_rejects_duplicate_ids(client, author_header):
    route = make_route(client, author_header).json()
    w1 = add_wp(client, author_header, route["id"], title="A").json()
    w2 = add_wp(client, author_header, route["id"], title="B").json()
    w3 = add_wp(client, author_header, route["id"], title="C").json()

    r = client.post(
        f"/routes/{route['id']}/waypoints/reorder",
        headers=author_header,
        json={"ordered_ids": [w1["id"], w1["id"], w3["id"]]},
    )
    assert r.status_code == 404

    # порядок не тронут дубликатом из предыдущего запроса
    unchanged = client.get(f"/routes/{route['id']}", headers=author_header).json()
    assert [w["title"] for w in unchanged["waypoints"]] == ["A", "B", "C"]
    assert [w1["order_index"], w2["order_index"], w3["order_index"]] == [0, 1, 2]


def test_stranger_cannot_edit(client, author_header):
    route = make_route(client, author_header).json()
    assert (
        client.patch(
            f"/routes/{route['id']}",
            headers=auth_header(role="local_historian"),
            json={"title": "x"},
        ).status_code
        == 403
    )
    # администратор может
    assert (
        client.patch(
            f"/routes/{route['id']}", headers=auth_header(is_root=True), json={"city": "Кромы"}
        ).status_code
        == 200
    )


def test_route_detail_includes_waypoints(client, author_header):
    route = make_route(client, author_header).json()
    add_wp(client, author_header, route["id"], title="A")
    add_wp(client, author_header, route["id"], title="B")
    client.post(
        f"/routes/{route['id']}/publish", headers=author_header, json={"is_published": True}
    )

    detail = client.get(f"/routes/{route['id']}").json()
    assert [w["title"] for w in detail["waypoints"]] == ["A", "B"]


def test_get_missing_404(client):
    assert client.get(f"/routes/{uuid.uuid4()}").status_code == 404
