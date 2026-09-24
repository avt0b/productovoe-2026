"""POST /family-links/invite · /redeem, GET /family-links/mine, DELETE .../{id}."""

from conftest import auth_header


def test_invite_then_redeem_links_both_ways(client):
    parent = auth_header(user_id="parent-1")
    child = auth_header(user_id="child-1")

    client.put("/profiles/me", headers=parent, json={"display_name": "Мама", "city": "Орёл"})
    client.put("/profiles/me", headers=child, json={"display_name": "Сын", "city": "Орёл"})

    invite = client.post("/family-links/invite", headers=parent).json()
    assert len(invite["code"]) == 8

    r = client.post("/family-links/redeem", headers=child, json={"code": invite["code"]})
    assert r.status_code == 204

    parent_family = client.get("/family-links/mine", headers=parent).json()
    assert [m["member_id"] for m in parent_family] == ["child-1"]
    assert parent_family[0]["display_name"] == "Сын"

    child_family = client.get("/family-links/mine", headers=child).json()
    assert [m["member_id"] for m in child_family] == ["parent-1"]
    assert child_family[0]["display_name"] == "Мама"


def test_redeem_unknown_code_404(client):
    r = client.post(
        "/family-links/redeem", headers=auth_header(user_id="u1"), json={"code": "ZZZZZZZZ"}
    )
    assert r.status_code == 404


def test_redeem_own_code_conflicts(client):
    parent = auth_header(user_id="parent-1")
    invite = client.post("/family-links/invite", headers=parent).json()
    r = client.post("/family-links/redeem", headers=parent, json={"code": invite["code"]})
    assert r.status_code == 409


def test_redeem_used_code_conflicts(client):
    parent = auth_header(user_id="parent-1")
    invite = client.post("/family-links/invite", headers=parent).json()
    client.post("/family-links/redeem", headers=auth_header(user_id="child-1"), json={"code": invite["code"]})

    r = client.post(
        "/family-links/redeem", headers=auth_header(user_id="child-2"), json={"code": invite["code"]}
    )
    assert r.status_code == 409


def test_remove_unlinks_both_ways(client):
    parent = auth_header(user_id="parent-1")
    child = auth_header(user_id="child-1")
    invite = client.post("/family-links/invite", headers=parent).json()
    client.post("/family-links/redeem", headers=child, json={"code": invite["code"]})

    r = client.delete("/family-links/child-1", headers=parent)
    assert r.status_code == 204

    assert client.get("/family-links/mine", headers=parent).json() == []
    assert client.get("/family-links/mine", headers=child).json() == []


def test_remove_missing_link_404(client):
    r = client.delete("/family-links/nobody", headers=auth_header(user_id="u1"))
    assert r.status_code == 404


def test_family_links_require_auth(client):
    assert client.post("/family-links/invite").status_code in (401, 403)
    assert client.get("/family-links/mine").status_code in (401, 403)
