import uuid

from conftest import auth_header


def test_get_me_creates_profile_lazily(client):
    uid = str(uuid.uuid4())
    r = client.get("/profiles/me", headers=auth_header(user_id=uid, role="searcher"))
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == uid
    assert body["role"] == "searcher"
    assert body["alert_radius_km"] == 20
    assert body["is_verified"] is False


def test_update_me(client):
    uid = str(uuid.uuid4())
    h = auth_header(user_id=uid)
    client.get("/profiles/me", headers=h)
    r = client.put(
        "/profiles/me",
        headers=h,
        json={
            "display_name": "Отряд Высота",
            "city": "Орёл",
            "subscribed_to_search": True,
            "alert_radius_km": 30,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["display_name"] == "Отряд Высота"
    assert body["city"] == "Орёл"
    assert body["subscribed_to_search"] is True
    assert body["alert_radius_km"] == 30


def test_update_me_rejects_bad_radius(client):
    h = auth_header()
    client.get("/profiles/me", headers=h)
    assert client.put("/profiles/me", headers=h, json={"alert_radius_km": 9999}).status_code == 422


def test_get_other_profile_requires_auth(client):
    assert client.get(f"/profiles/{uuid.uuid4()}").status_code in (401, 403)


def test_get_missing_profile_404(client):
    r = client.get(f"/profiles/{uuid.uuid4()}", headers=auth_header())
    assert r.status_code == 404


def test_list_profiles_root_only(client):
    assert client.get("/profiles", headers=auth_header(role="searcher")).status_code == 403
    assert client.get("/profiles", headers=auth_header(is_root=True)).status_code == 200


def test_verify_profile_permissions(client):
    target = str(uuid.uuid4())
    client.get("/profiles/me", headers=auth_header(user_id=target))

    # family не может
    assert (
        client.patch(
            f"/profiles/{target}/verify",
            headers=auth_header(role="family"),
            json={"is_verified": True},
        ).status_code
        == 403
    )

    # краевед (пиринговая верификация) больше не может — только администратор
    assert (
        client.patch(
            f"/profiles/{target}/verify",
            headers=auth_header(role="local_historian"),
            json={"is_verified": True},
        ).status_code
        == 403
    )

    # администратор может
    r = client.patch(
        f"/profiles/{target}/verify",
        headers=auth_header(is_root=True),
        json={"is_verified": True},
    )
    assert r.status_code == 200
    assert r.json()["is_verified"] is True
