import uuid

from conftest import WORKER_HEADER, auth_header


def make_clip(client, header, **over):
    body = {
        "soldier_name": "Иванов И.И.",
        "source_photo_url": "https://archive.example/ivanov.jpg",
        "consent_memorial_use": True,
    }
    body.update(over)
    return client.post("/clips", headers=header, json=body)


def render_ready(client, clip_id, url="https://cdn.example/clip.mp4"):
    client.post(f"/render/{clip_id}/ready", headers=WORKER_HEADER, json={"video_url": url})


def test_narration_pulls_feat_text_from_archive_entry(client, monkeypatch):
    import services.clip_service as clip_service_module

    async def fake_fetch(entry_id):
        assert entry_id == "entry-1"
        return {"id": "entry-1", "body": "Подорвал два танка под Орлом ценой своей жизни."}

    monkeypatch.setattr(clip_service_module, "fetch_entry", fake_fetch)

    r = make_clip(client, auth_header(), archive_entry_id="entry-1")
    assert r.status_code == 201
    text = r.json()["narration_text"]
    assert "голубое небо" in text
    assert "Подорвал два танка" in text


def test_narration_falls_back_to_default_when_archive_unavailable(client, monkeypatch):
    import services.clip_service as clip_service_module

    async def fake_fetch(entry_id):
        return None

    monkeypatch.setattr(clip_service_module, "fetch_entry", fake_fetch)

    r = make_clip(client, auth_header(), archive_entry_id="missing")
    assert r.json()["narration_text"] == "Я сделал это, чтобы ты жил и видел голубое небо. Помни меня."


def test_explicit_narration_text_is_not_overridden(client, monkeypatch):
    import services.clip_service as clip_service_module

    async def fake_fetch(entry_id):
        raise AssertionError("archive_service не должен вызываться, если текст передан явно")

    monkeypatch.setattr(clip_service_module, "fetch_entry", fake_fetch)

    r = make_clip(
        client, auth_header(), archive_entry_id="entry-1", narration_text="Свой текст"
    )
    assert r.json()["narration_text"] == "Свой текст"


def test_create_requires_consent(client):
    assert make_clip(client, auth_header(), consent_memorial_use=False).status_code == 403
    r = make_clip(client, auth_header())
    assert r.status_code == 201
    assert r.json()["status"] == "queued"
    assert "голубое небо" in r.json()["narration_text"]


def test_create_without_consent_field_also_403_not_422(client):
    # Пропущенное поле — тот же отказ, что и явный False, а не 422 от pydantic.
    body = {
        "soldier_name": "Иванов И.И.",
        "source_photo_url": "https://archive.example/ivanov.jpg",
    }
    r = client.post("/clips", headers=auth_header(), json=body)
    assert r.status_code == 403


def test_create_requires_auth(client):
    assert make_clip(client, {}).status_code in (401, 403)


def test_public_gallery_shows_only_public_ready(client):
    author = auth_header(user_id="a1")
    c = make_clip(client, author, is_public=True).json()
    assert client.get("/clips").json() == []  # ещё queued

    render_ready(client, c["id"])
    gallery = client.get("/clips").json()
    assert [x["id"] for x in gallery] == [c["id"]]
    assert gallery[0]["video_url"]


def test_private_clip_hidden_from_strangers(client):
    author = auth_header(user_id="a1")
    c = make_clip(client, author, is_public=False).json()
    render_ready(client, c["id"])

    assert client.get(f"/clips/{c['id']}", headers=author).status_code == 200
    assert (
        client.get(f"/clips/{c['id']}", headers=auth_header(user_id="stranger")).status_code == 404
    )
    assert client.get(f"/clips/{c['id']}").status_code == 404
    # администратор видит
    assert client.get(f"/clips/{c['id']}", headers=auth_header(is_root=True)).status_code == 200


def test_worker_claim_and_lifecycle(client):
    author = auth_header(user_id="a1")
    c1 = make_clip(client, author, soldier_name="Первый").json()
    make_clip(client, author, soldier_name="Второй")

    claimed = client.post("/render/claim", headers=WORKER_HEADER).json()
    assert claimed["id"] == c1["id"]
    assert claimed["status"] == "processing"

    done = client.post(
        f"/render/{c1['id']}/ready", headers=WORKER_HEADER, json={"video_url": "https://cdn/x.mp4"}
    ).json()
    assert done["status"] == "ready"
    assert done["rendered_at"]


def test_worker_endpoints_reject_normal_user(client):
    c = make_clip(client, auth_header()).json()
    assert client.post("/render/claim", headers=auth_header(role="family")).status_code == 403
    assert (
        client.post(
            f"/render/{c['id']}/ready", headers=auth_header(role="family"), json={"video_url": "x"}
        ).status_code
        == 403
    )
    # администратор может без worker-токена
    assert client.post("/render/claim", headers=auth_header(is_root=True)).status_code in (
        200,
        204,
    )


def test_failed_then_retry(client):
    author = auth_header(user_id="a1")
    c = make_clip(client, author).json()
    client.post(
        f"/render/{c['id']}/failed", headers=WORKER_HEADER, json={"error": "no face detected"}
    )
    assert client.get(f"/clips/{c['id']}", headers=author).json()["status"] == "failed"

    retried = client.post(f"/clips/{c['id']}/retry", headers=author).json()
    assert retried["status"] == "queued"
    assert retried["error"] == ""


def test_cannot_edit_while_processing(client):
    author = auth_header(user_id="a1")
    c = make_clip(client, author).json()
    client.post("/render/claim", headers=WORKER_HEADER)  # -> processing
    r = client.patch(f"/clips/{c['id']}", headers=author, json={"narration_text": "новый текст"})
    assert r.status_code == 409


def test_share_only_when_ready(client):
    author = auth_header(user_id="a1")
    c = make_clip(client, author).json()
    assert (
        client.post(
            f"/clips/{c['id']}/shares", headers=author, json={"recipient": "внучка, vk.com/x"}
        ).status_code
        == 409
    )

    render_ready(client, c["id"])
    s = client.post(
        f"/clips/{c['id']}/shares",
        headers=author,
        json={"recipient": "внучка, vk.com/x", "note": "нашли через поисковый отряд"},
    )
    assert s.status_code == 201
    shares = client.get(f"/clips/{c['id']}/shares", headers=author).json()
    assert len(shares) == 1 and shares[0]["recipient"].startswith("внучка")


def test_mine_lists_all_statuses(client):
    author = auth_header(user_id="a1")
    make_clip(client, author)
    c2 = make_clip(client, author).json()
    render_ready(client, c2["id"])
    mine = client.get("/clips/mine", headers=author).json()
    assert {m["status"] for m in mine} == {"queued", "ready"}


def test_get_missing_404(client):
    assert client.get(f"/clips/{uuid.uuid4()}", headers=auth_header()).status_code == 404
