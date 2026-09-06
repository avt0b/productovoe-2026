from conftest import auth_headers, login

NEW_ADMIN = {
    "email": "moderator@marshruty.ru",
    "password": "moderator-strong-pass",
    "full_name": "Модератор архива",
    "role": "moderator",
}


def test_superadmin_creates_and_lists_accounts(client, superadmin):
    headers = auth_headers(client)

    created = client.post("/admin/accounts", headers=headers, json=NEW_ADMIN)
    assert created.status_code == 201
    assert created.json()["role"] == "moderator"

    listed = client.get("/admin/accounts", headers=headers).json()
    assert listed["total"] == 2
    assert {a["email"] for a in listed["items"]} == {
        superadmin.email,
        NEW_ADMIN["email"],
    }


def test_duplicate_email_is_rejected(client, superadmin):
    headers = auth_headers(client)
    client.post("/admin/accounts", headers=headers, json=NEW_ADMIN)
    again = client.post("/admin/accounts", headers=headers, json=NEW_ADMIN)
    assert again.status_code == 409


def test_viewer_cannot_manage_accounts(client, superadmin):
    headers = auth_headers(client)
    viewer = {**NEW_ADMIN, "email": "viewer@marshruty.ru", "role": "viewer"}
    client.post("/admin/accounts", headers=headers, json=viewer)

    viewer_headers = auth_headers(client, email=viewer["email"], password=viewer["password"])
    assert client.get("/admin/accounts", headers=viewer_headers).status_code == 403
    # …но дашборд и журнал наблюдателю доступны.
    assert client.get("/admin/audit", headers=viewer_headers).status_code == 200


def test_cannot_disable_last_superadmin(client, superadmin):
    headers = auth_headers(client)
    other = {**NEW_ADMIN, "email": "second@marshruty.ru", "role": "superadmin"}
    created = client.post("/admin/accounts", headers=headers, json=other).json()

    # Второго суперадмина отключить можно — первый остаётся.
    assert client.patch(
        f"/admin/accounts/{created['id']}/active",
        headers=headers,
        json={"is_active": False},
    ).status_code == 200

    # А себя — нельзя ни в каком случае.
    blocked = client.patch(
        f"/admin/accounts/{superadmin.id}/active",
        headers=headers,
        json={"is_active": False},
    )
    assert blocked.status_code == 403


def test_disabled_account_loses_access(client, superadmin):
    headers = auth_headers(client)
    created = client.post("/admin/accounts", headers=headers, json=NEW_ADMIN).json()
    assert login(
        client, email=NEW_ADMIN["email"], password=NEW_ADMIN["password"]
    ).status_code == 200

    client.patch(
        f"/admin/accounts/{created['id']}/active", headers=headers, json={"is_active": False}
    )
    assert login(
        client, email=NEW_ADMIN["email"], password=NEW_ADMIN["password"]
    ).status_code == 403


def test_actions_are_written_to_audit_log(client, superadmin):
    headers = auth_headers(client)
    client.post("/admin/accounts", headers=headers, json=NEW_ADMIN)

    log = client.get("/admin/audit", headers=headers).json()
    actions = [row["action"] for row in log["items"]]
    assert "admin.account.create" in actions
    assert "admin.login" in actions

    created_row = next(r for r in log["items"] if r["action"] == "admin.account.create")
    assert created_row["actor_email"] == superadmin.email
    assert created_row["target_label"] == NEW_ADMIN["email"]
    assert created_row["outcome"] == "success"
