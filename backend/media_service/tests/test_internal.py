from conftest import WORKER_HEADER, auth_header

from core.config import settings

INTERNAL_HEADER = {"X-Internal-Key": settings.internal_api_key}


def make_clip(client, header=None, **over):
    header = header or auth_header()
    body = {
        "soldier_name": "Иванов И.И.",
        "source_photo_url": "https://archive.example/ivanov.jpg",
        "consent_memorial_use": True,
    }
    body.update(over)
    return client.post("/clips", headers=header, json=body)


def render_ready(client, clip_id, url="https://cdn.example/clip.mp4"):
    client.post(f"/render/{clip_id}/ready", headers=WORKER_HEADER, json={"video_url": url})


def render_failed(client, clip_id, error="no face detected"):
    client.post(f"/render/{clip_id}/failed", headers=WORKER_HEADER, json={"error": error})


# --- проверка ключа ---


def test_stats_requires_internal_key(client):
    assert client.get("/internal/stats").status_code == 403


def test_stats_rejects_wrong_key(client):
    r = client.get("/internal/stats", headers={"X-Internal-Key": "wrong-key"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Недействительный внутренний ключ"


def test_list_clips_requires_internal_key(client):
    assert client.get("/internal/clips").status_code == 403


def test_update_clip_requires_internal_key(client):
    c = make_clip(client).json()
    r = client.patch(f"/internal/clips/{c['id']}", json={"is_public": True})
    assert r.status_code == 403


def test_retry_requires_internal_key(client):
    c = make_clip(client).json()
    r = client.post(f"/internal/clips/{c['id']}/retry")
    assert r.status_code == 403


def test_delete_requires_internal_key(client):
    c = make_clip(client).json()
    r = client.delete(f"/internal/clips/{c['id']}")
    assert r.status_code == 403


# --- /internal/stats ---


def test_stats_shape(client):
    author = auth_header(user_id="a1")
    c1 = make_clip(client, author, is_public=True).json()
    render_ready(client, c1["id"])
    make_clip(client, author)  # queued
    c3 = make_clip(client, author).json()
    render_failed(client, c3["id"])
    client.post(
        f"/clips/{c1['id']}/shares", headers=author, json={"recipient": "внучка"}
    )

    r = client.get("/internal/stats", headers=INTERNAL_HEADER)
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "media_service"
    assert data["clips_total"] == 3
    assert data["by_status"]["ready"] == 1
    assert data["by_status"]["queued"] == 1
    assert data["by_status"]["failed"] == 1
    assert data["queue_depth"] == 1  # queued + processing
    assert data["failed"] == 1
    assert data["public"] == 1
    assert data["shares_total"] == 1
    assert data["created_7d"] == 3


# --- /internal/clips ---


def test_list_clips_sees_all_statuses_and_private(client):
    author = auth_header(user_id="a1")
    c = make_clip(client, author, is_public=False).json()  # queued & private

    r = client.get("/internal/clips", headers=INTERNAL_HEADER)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["limit"] == 50
    assert data["offset"] == 0
    assert [item["id"] for item in data["items"]] == [c["id"]]
    assert data["items"][0]["status"] == "queued"
    assert data["items"][0]["is_public"] is False


def test_list_clips_filters_by_status_is_public_and_query(client):
    author = auth_header(user_id="a1")
    ready = make_clip(client, author, soldier_name="Петров П.П.", is_public=True).json()
    render_ready(client, ready["id"])
    queued = make_clip(client, author, soldier_name="Сидоров С.С.").json()

    r = client.get("/internal/clips", headers=INTERNAL_HEADER, params={"status": "ready"})
    assert [x["id"] for x in r.json()["items"]] == [ready["id"]]

    r = client.get("/internal/clips", headers=INTERNAL_HEADER, params={"is_public": "true"})
    assert [x["id"] for x in r.json()["items"]] == [ready["id"]]

    r = client.get("/internal/clips", headers=INTERNAL_HEADER, params={"query": "Сидоров"})
    assert [x["id"] for x in r.json()["items"]] == [queued["id"]]


# --- мутации через internal_actor ---


def test_internal_update_bypasses_ownership_and_processing_lock(client):
    author = auth_header(user_id="a1")
    c = make_clip(client, author).json()
    client.post("/render/claim", headers=WORKER_HEADER)  # -> processing

    # обычный автор не может править клип в обработке
    assert client.patch(
        f"/clips/{c['id']}", headers=author, json={"narration_text": "x"}
    ).status_code == 409

    # internal actor правит несмотря на processing и без владения клипом
    r = client.patch(
        f"/internal/clips/{c['id']}",
        headers={**INTERNAL_HEADER, "X-Actor-Id": "admin-1"},
        json={"is_public": False, "narration_text": "снято с публикации"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["is_public"] is False
    assert body["narration_text"] == "снято с публикации"


def test_internal_retry_only_when_failed(client):
    author = auth_header(user_id="a1")
    c = make_clip(client, author).json()  # queued, not failed

    r = client.post(
        f"/internal/clips/{c['id']}/retry",
        headers={**INTERNAL_HEADER, "X-Actor-Id": "admin-1"},
    )
    assert r.status_code == 409

    render_failed(client, c["id"])
    r = client.post(
        f"/internal/clips/{c['id']}/retry",
        headers={**INTERNAL_HEADER, "X-Actor-Id": "admin-1"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "queued"
    assert body["error"] == ""


def test_internal_delete_bypasses_ownership(client):
    other_owner = auth_header(user_id="someone-else")
    c = make_clip(client, other_owner).json()

    r = client.delete(
        f"/internal/clips/{c['id']}",
        headers={**INTERNAL_HEADER, "X-Actor-Id": "admin-1"},
    )
    assert r.status_code == 204
    assert client.get(f"/clips/{c['id']}", headers=other_owner).status_code == 404


def test_internal_update_missing_clip_404(client):
    r = client.patch(
        "/internal/clips/does-not-exist",
        headers=INTERNAL_HEADER,
        json={"is_public": True},
    )
    assert r.status_code == 404
