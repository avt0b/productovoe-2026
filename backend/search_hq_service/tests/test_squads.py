from conftest import auth_header


def create_squad(client, header, **over):
    body = {"name": "Отряд «Высота»", "region": "Орловская область", "contact": "vk.com/vysota"}
    body.update(over)
    return client.post("/squads", headers=header, json=body)


def test_only_searcher_or_moderator_creates(client):
    assert create_squad(client, auth_header(role="family")).status_code == 403
    assert create_squad(client, auth_header(role="searcher")).status_code == 201
    assert create_squad(client, auth_header(role="moderator")).status_code == 201


def test_leader_is_set_from_token(client, leader_header):
    r = create_squad(client, leader_header)
    assert r.json()["leader_id"] == "leader-1"


def test_only_leader_or_staff_edits(client, leader_header):
    squad = create_squad(client, leader_header).json()

    other = auth_header(role="searcher")
    assert client.patch(f"/squads/{squad['id']}", headers=other, json={"name": "x"}).status_code == 403

    assert client.patch(
        f"/squads/{squad['id']}", headers=leader_header, json={"name": "Высота-2"}
    ).status_code == 200
    assert client.patch(
        f"/squads/{squad['id']}", headers=auth_header(is_root=True), json={"region": "Орёл"}
    ).status_code == 200


def test_list_and_filter_by_region(client):
    create_squad(client, auth_header(role="searcher"), name="A", region="Орловская область")
    create_squad(client, auth_header(role="searcher"), name="B", region="Тульская область")
    rows = client.get("/squads", params={"region": "Орлов"}).json()
    assert [s["name"] for s in rows] == ["A"]


def test_delete_by_leader(client, leader_header):
    squad = create_squad(client, leader_header).json()
    assert client.delete(f"/squads/{squad['id']}", headers=leader_header).status_code == 204
    assert client.get(f"/squads/{squad['id']}").status_code == 404
