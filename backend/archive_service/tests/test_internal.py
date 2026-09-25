from conftest import auth_header

from core.config import settings

INTERNAL_HEADER = {"X-Internal-Key": settings.internal_api_key}


def create_entry(client, header=None, **over):
    header = header or auth_header()
    body = {
        "kind": "event",
        "title": "Десант 5-го вдк под Орлом",
        "body": "Октябрь 1941, 9, 10, 201-я бригады задержали врага.",
        "date_text": "октябрь 1941",
        "lat": 52.9686,
        "lon": 36.0694,
    }
    body.update(over)
    return client.post("/entries", headers=header, json=body)


# --- проверка ключа ---


def test_stats_requires_internal_key(client):
    assert client.get("/internal/stats").status_code == 403


def test_stats_rejects_wrong_key(client):
    r = client.get("/internal/stats", headers={"X-Internal-Key": "wrong-key"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Недействительный внутренний ключ"


def test_list_entries_requires_internal_key(client):
    assert client.get("/internal/entries").status_code == 403


def test_verify_requires_internal_key(client):
    e = create_entry(client, auth_header(user_id="author-1")).json()
    r = client.post(f"/internal/entries/{e['id']}/verify", json={})
    assert r.status_code == 403


def test_reject_requires_internal_key(client):
    e = create_entry(client, auth_header(user_id="author-1")).json()
    r = client.post(f"/internal/entries/{e['id']}/reject", json={})
    assert r.status_code == 403


def test_delete_requires_internal_key(client):
    e = create_entry(client, auth_header(user_id="author-1")).json()
    r = client.delete(f"/internal/entries/{e['id']}")
    assert r.status_code == 403


def test_timeseries_requires_internal_key(client):
    assert client.get("/internal/stats/timeseries").status_code == 403


# --- /internal/stats ---


def test_stats_shape(client):
    author = auth_header(user_id="author-1")
    e = create_entry(client, author).json()
    client.post(
        f"/entries/{e['id']}/verify",
        headers=auth_header(role="local_historian"),
        json={"note": "проверено"},
    )
    create_entry(client, auth_header(user_id="author-2"), title="Ещё одна запись")

    r = client.get("/internal/stats", headers=INTERNAL_HEADER)
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "archive_service"
    assert data["entries_total"] == 2
    assert data["by_status"]["verified"] == 1
    assert data["by_status"]["pending"] == 1
    assert data["by_kind"]["event"] == 2
    assert data["moderation_queue"] == 1
    assert data["verified_7d"] == 1
    assert data["submitted_7d"] == 2
    assert data["geo_tagged"] == 2


def test_stats_timeseries_shape(client):
    author = auth_header(user_id="author-1")
    e = create_entry(client, author).json()
    client.post(
        f"/entries/{e['id']}/verify",
        headers=auth_header(role="local_historian"),
        json={"note": "ok"},
    )

    r = client.get("/internal/stats/timeseries", headers=INTERNAL_HEADER)
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "archive_service"
    assert data["days"] == 30
    assert isinstance(data["points"], list)
    assert len(data["points"]) == 1
    assert data["points"][0]["value"] == 1


# --- /internal/entries ---


def test_list_entries_sees_pending_and_all_statuses(client):
    author = auth_header(user_id="author-1")
    e = create_entry(client, author).json()

    r = client.get("/internal/entries", headers=INTERNAL_HEADER)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["limit"] == 50
    assert data["offset"] == 0
    assert [item["id"] for item in data["items"]] == [e["id"]]
    # /internal видит полную схему, включая review_note (не EntryPublicOut)
    assert "review_note" in data["items"][0]
    assert data["items"][0]["status"] == "pending"


def test_list_entries_filters_by_status_and_kind(client):
    author = auth_header(user_id="author-1")
    pending = create_entry(client, author).json()
    verified_src = create_entry(client, author, title="Вторая запись").json()
    client.post(
        f"/entries/{verified_src['id']}/verify",
        headers=auth_header(role="local_historian"),
        json={},
    )

    r = client.get("/internal/entries", headers=INTERNAL_HEADER, params={"status": "pending"})
    assert [x["id"] for x in r.json()["items"]] == [pending["id"]]

    r = client.get("/internal/entries", headers=INTERNAL_HEADER, params={"status": "verified"})
    assert [x["id"] for x in r.json()["items"]] == [verified_src["id"]]

    r = client.get("/internal/entries", headers=INTERNAL_HEADER, params={"query": "Вторая"})
    assert [x["id"] for x in r.json()["items"]] == [verified_src["id"]]


# --- мутации через internal_actor ---


def test_internal_verify_bypasses_role_restrictions(client):
    e = create_entry(client, auth_header(user_id="author-1")).json()
    # без ключа + без роли verifier — но internal actor is_root=True
    r = client.post(
        f"/internal/entries/{e['id']}/verify",
        headers={**INTERNAL_HEADER, "X-Actor-Id": "admin-42"},
        json={"note": "подтверждено штабом"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "verified"
    assert body["verified_by"] == "admin-42"
    assert body["review_note"] == "подтверждено штабом"


def test_internal_verify_defaults_actor_to_admin(client):
    e = create_entry(client, auth_header(user_id="author-1")).json()
    r = client.post(
        f"/internal/entries/{e['id']}/verify",
        headers=INTERNAL_HEADER,
        json={},
    )
    assert r.status_code == 200
    assert r.json()["verified_by"] == "admin"


def test_internal_reject_bypasses_role_restrictions(client):
    e = create_entry(client, auth_header(user_id="author-1")).json()
    r = client.post(
        f"/internal/entries/{e['id']}/reject",
        headers={**INTERNAL_HEADER, "X-Actor-Id": "admin-7"},
        json={"note": "дубликат"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "rejected"
    assert body["verified_by"] == "admin-7"
    assert body["review_note"] == "дубликат"


def test_internal_delete_removes_entry_even_when_not_pending(client):
    e = create_entry(client, auth_header(user_id="author-1")).json()
    client.post(f"/entries/{e['id']}/verify", headers=auth_header(role="local_historian"), json={})

    r = client.delete(
        f"/internal/entries/{e['id']}",
        headers={**INTERNAL_HEADER, "X-Actor-Id": "admin-1"},
    )
    assert r.status_code == 204

    # запись реально удалена, обычный autor больше её не видит
    assert (
        client.get(f"/entries/{e['id']}", headers=auth_header(user_id="author-1")).status_code
        == 404
    )


def test_internal_delete_logs_non_pending_deletion(client, caplog):
    e = create_entry(client, auth_header(user_id="author-1")).json()
    client.post(f"/entries/{e['id']}/verify", headers=auth_header(role="local_historian"), json={})

    with caplog.at_level("WARNING"):
        r = client.delete(
            f"/internal/entries/{e['id']}",
            headers={**INTERNAL_HEADER, "X-Actor-Id": "admin-9"},
        )
    assert r.status_code == 204
    assert any(
        e["id"] in record.getMessage() and "admin-9" in record.getMessage()
        for record in caplog.records
    )


def test_internal_verify_missing_entry_404(client):
    r = client.post(
        "/internal/entries/does-not-exist/verify",
        headers=INTERNAL_HEADER,
        json={},
    )
    assert r.status_code == 404
