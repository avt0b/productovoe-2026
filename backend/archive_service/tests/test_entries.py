import uuid

from conftest import auth_header


def create_entry(client, header, **over):
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


def test_create_is_pending(client):
    r = create_entry(client, auth_header(role="family"))
    assert r.status_code == 201
    assert r.json()["status"] == "pending"
    assert r.json()["submitted_by"]


def test_create_requires_auth(client):
    assert create_entry(client, {}).status_code in (401, 403)


def test_coords_must_come_together(client):
    r = create_entry(client, auth_header(), lat=52.9, lon=None)
    assert r.status_code == 422


def test_public_feed_shows_only_verified(client):
    author = auth_header(user_id="author-1")
    e = create_entry(client, author).json()
    assert client.get("/entries").json() == []

    client.post(
        f"/entries/{e['id']}/verify",
        headers=auth_header(role="local_historian"),
        json={"note": "сверено с Книгой Памяти Т. 5"},
    )
    feed = client.get("/entries").json()
    assert [x["id"] for x in feed] == [e["id"]]
    assert feed[0]["status"] == "verified"
    assert feed[0]["verified_by"]


def test_pending_entry_visible_to_author_and_verifier_only(client):
    author = auth_header(user_id="author-1")
    e = create_entry(client, author).json()

    # автор видит
    assert client.get(f"/entries/{e['id']}", headers=author).status_code == 200
    # верификатор видит
    assert (
        client.get(f"/entries/{e['id']}", headers=auth_header(role="local_historian")).status_code == 200
    )
    # посторонний — 404
    assert (
        client.get(f"/entries/{e['id']}", headers=auth_header(user_id="stranger")).status_code
        == 404
    )
    # аноним — 404
    assert client.get(f"/entries/{e['id']}").status_code == 404


def test_verify_permissions(client):
    e = create_entry(client, auth_header(user_id="author-1")).json()
    assert (
        client.post(
            f"/entries/{e['id']}/verify", headers=auth_header(role="family"), json={}
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/entries/{e['id']}/verify", headers=auth_header(role="local_historian"), json={}
        ).status_code
        == 200
    )


def test_verify_awards_archive_helper_achievement(client, monkeypatch):
    import services.entry_service as entry_service_module

    calls = []
    monkeypatch.setattr(
        entry_service_module, "award_achievement", lambda **kw: calls.append(kw)
    )

    e = create_entry(client, auth_header(user_id="author-1")).json()
    client.post(
        f"/entries/{e['id']}/verify", headers=auth_header(role="local_historian", user_id="mod-1"), json={}
    )
    assert calls == [{"user_id": "mod-1", "code": "archive_helper"}]


def test_reject_also_awards_archive_helper_achievement(client, monkeypatch):
    import services.entry_service as entry_service_module

    calls = []
    monkeypatch.setattr(
        entry_service_module, "award_achievement", lambda **kw: calls.append(kw)
    )

    e = create_entry(client, auth_header(user_id="author-1")).json()
    client.post(
        f"/entries/{e['id']}/reject", headers=auth_header(role="local_historian", user_id="mod-1"), json={}
    )
    assert calls == [{"user_id": "mod-1", "code": "archive_helper"}]


def test_verify_credits_finds_stat_to_author_not_verifier(client, monkeypatch):
    import services.entry_service as entry_service_module

    calls = []
    monkeypatch.setattr(
        entry_service_module, "increment_stat", lambda **kw: calls.append(kw)
    )

    e = create_entry(client, auth_header(user_id="author-1")).json()
    client.post(
        f"/entries/{e['id']}/verify", headers=auth_header(role="local_historian", user_id="mod-1"), json={}
    )
    assert calls == [{"user_id": "author-1", "metric": "finds_count"}]


def test_reject_does_not_credit_finds_stat(client, monkeypatch):
    import services.entry_service as entry_service_module

    calls = []
    monkeypatch.setattr(
        entry_service_module, "increment_stat", lambda **kw: calls.append(kw)
    )

    e = create_entry(client, auth_header(user_id="author-1")).json()
    client.post(
        f"/entries/{e['id']}/reject", headers=auth_header(role="local_historian", user_id="mod-1"), json={}
    )
    assert calls == []


def test_searcher_can_verify(client):
    e = create_entry(client, auth_header(user_id="author-1")).json()
    r = client.post(
        f"/entries/{e['id']}/verify", headers=auth_header(role="searcher"), json={}
    )
    assert r.status_code == 200
    assert r.json()["verified_by"]


def test_reject_with_note(client):
    e = create_entry(client, auth_header(user_id="author-1")).json()
    r = client.post(
        f"/entries/{e['id']}/reject",
        headers=auth_header(role="local_historian"),
        json={"note": "нет источника"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
    assert r.json()["review_note"] == "нет источника"


def test_review_note_hidden_from_public_visible_to_author_and_verifier(client):
    author = auth_header(user_id="author-1")
    e = create_entry(client, author).json()
    client.post(
        f"/entries/{e['id']}/verify",
        headers=auth_header(role="local_historian"),
        json={"note": "сверено с Книгой Памяти, но источник спорный"},
    )

    public_feed = client.get("/entries").json()
    assert "review_note" not in public_feed[0]

    public_single = client.get(f"/entries/{e['id']}").json()
    assert "review_note" not in public_single

    stranger_single = client.get(
        f"/entries/{e['id']}", headers=auth_header(user_id="stranger")
    ).json()
    assert "review_note" not in stranger_single

    author_single = client.get(f"/entries/{e['id']}", headers=author).json()
    assert author_single["review_note"] == "сверено с Книгой Памяти, но источник спорный"

    verifier_single = client.get(
        f"/entries/{e['id']}", headers=auth_header(role="local_historian")
    ).json()
    assert verifier_single["review_note"] == "сверено с Книгой Памяти, но источник спорный"


def test_author_cannot_edit_after_verify(client):
    author = auth_header(user_id="author-1")
    e = create_entry(client, author).json()

    assert (
        client.patch(f"/entries/{e['id']}", headers=author, json={"title": "поправка"}).status_code
        == 200
    )

    client.post(f"/entries/{e['id']}/verify", headers=auth_header(role="local_historian"), json={})
    assert (
        client.patch(
            f"/entries/{e['id']}", headers=author, json={"title": "ещё правка"}
        ).status_code
        == 409
    )


def test_moderation_queue_lists_pending(client):
    create_entry(client, auth_header(user_id="a1"))
    create_entry(client, auth_header(user_id="a2"))
    q = client.get("/entries/moderation", headers=auth_header(role="local_historian"))
    assert q.status_code == 200
    assert len(q.json()) == 2
    assert client.get("/entries/moderation", headers=auth_header(role="family")).status_code == 403


def test_mine_lists_all_statuses(client):
    author = auth_header(user_id="author-1")
    e = create_entry(client, author).json()
    client.post(f"/entries/{e['id']}/reject", headers=auth_header(role="local_historian"), json={})
    mine = client.get("/entries/mine", headers=author).json()
    assert [x["status"] for x in mine] == ["rejected"]


def test_delete_pending_by_author_then_gone(client):
    author = auth_header(user_id="author-1")
    e = create_entry(client, author).json()
    assert client.delete(f"/entries/{e['id']}", headers=author).status_code == 204
    assert client.get(f"/entries/{e['id']}", headers=author).status_code == 404


def test_get_missing_404(client):
    assert client.get(f"/entries/{uuid.uuid4()}").status_code == 404


def test_verifier_edit_after_review_restamps_reviewed_at(client):
    author = auth_header(user_id="author-1")
    e = create_entry(client, author).json()
    client.post(
        f"/entries/{e['id']}/verify",
        headers=auth_header(role="local_historian", user_id="hist-1"),
        json={"note": "сверено"},
    )

    edited = client.patch(
        f"/entries/{e['id']}",
        headers=auth_header(role="local_historian", user_id="mod-1"),
        json={"title": "уточнённый заголовок"},
    ).json()
    assert edited["title"] == "уточнённый заголовок"
    assert edited["status"] == "verified"
    assert edited["verified_by"] == "mod-1"
    # note от исходной верификации не трогаем — правка не переиспользует "verify"
    assert edited["review_note"] == "сверено"


def test_deleting_reviewed_entry_is_logged(client, caplog):
    e = create_entry(client, auth_header(user_id="author-1")).json()
    client.post(f"/entries/{e['id']}/verify", headers=auth_header(role="local_historian"), json={})

    with caplog.at_level("WARNING"):
        r = client.delete(
            f"/entries/{e['id']}", headers=auth_header(role="local_historian", user_id="mod-9")
        )
    assert r.status_code == 204
    assert any(
        e["id"] in record.getMessage() and "mod-9" in record.getMessage()
        for record in caplog.records
    )


def test_filter_by_point_and_poi(client):
    point_id = str(uuid.uuid4())
    poi_id = str(uuid.uuid4())
    author = auth_header(user_id="author-1")

    to_point = create_entry(client, author, point_id=point_id).json()
    to_poi = create_entry(client, author, poi_id=poi_id).json()
    unrelated = create_entry(client, author).json()

    for entry in (to_point, to_poi, unrelated):
        client.post(
            f"/entries/{entry['id']}/verify", headers=auth_header(role="local_historian"), json={}
        )

    by_point = client.get("/entries", params={"point_id": point_id}).json()
    assert [e["id"] for e in by_point] == [to_point["id"]]

    by_poi = client.get("/entries", params={"poi_id": poi_id}).json()
    assert [e["id"] for e in by_poi] == [to_poi["id"]]
