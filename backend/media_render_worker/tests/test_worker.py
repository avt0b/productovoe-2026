import worker
from clients.lipsync import RenderFailed

CLIP = {
    "id": "clip-1",
    "narration_text": "Я сделал это, чтобы ты жил.",
    "voice_style": "era_male",
    "source_photo_url": "https://minio.local/media/photo.jpg",
}


def test_process_one_returns_false_when_queue_empty(monkeypatch):
    monkeypatch.setattr(worker.media_service, "claim_next", lambda: None)
    assert worker.process_one() is False


def test_process_one_happy_path(monkeypatch):
    calls = {}

    monkeypatch.setattr(worker.media_service, "claim_next", lambda: dict(CLIP))
    monkeypatch.setattr(worker.speechkit, "synthesize", lambda text, voice: b"WAV-BYTES")
    monkeypatch.setattr(
        worker.lipsync, "animate", lambda **kw: "https://replicate.delivery/video.mp4"
    )
    monkeypatch.setattr(worker, "_download", lambda url: b"MP4-BYTES")
    monkeypatch.setattr(
        worker.storage,
        "upload_video",
        lambda **kw: "https://minio.local/media/rendered/clip-1.mp4",
    )
    monkeypatch.setattr(
        worker.media_service,
        "mark_ready",
        lambda clip_id, *, video_url: calls.setdefault("ready", (clip_id, video_url)),
    )

    assert worker.process_one() is True
    assert calls["ready"] == ("clip-1", "https://minio.local/media/rendered/clip-1.mp4")


def test_process_one_marks_failed_on_render_error(monkeypatch):
    calls = {}

    monkeypatch.setattr(worker.media_service, "claim_next", lambda: dict(CLIP))
    monkeypatch.setattr(worker.speechkit, "synthesize", lambda text, voice: b"WAV-BYTES")

    def boom(**kw):
        raise RenderFailed("модель недоступна")

    monkeypatch.setattr(worker.lipsync, "animate", boom)
    monkeypatch.setattr(
        worker.media_service,
        "mark_failed",
        lambda clip_id, *, error: calls.setdefault("failed", (clip_id, error)),
    )

    assert worker.process_one() is True
    assert calls["failed"] == ("clip-1", "модель недоступна")


def test_process_one_marks_failed_on_network_error(monkeypatch):
    import httpx

    calls = {}

    monkeypatch.setattr(worker.media_service, "claim_next", lambda: dict(CLIP))

    def boom(text, voice):
        raise httpx.ConnectError("no route to host")

    monkeypatch.setattr(worker.speechkit, "synthesize", boom)
    monkeypatch.setattr(
        worker.media_service,
        "mark_failed",
        lambda clip_id, *, error: calls.setdefault("failed", (clip_id, error)),
    )

    assert worker.process_one() is True
    assert calls["failed"][0] == "clip-1"
    assert "ConnectError" in calls["failed"][1]


def test_voice_style_falls_back_to_neutral_for_unknown_code():
    from clients.speechkit import VOICE_BY_STYLE

    assert VOICE_BY_STYLE.get("something-unexpected", "filipp") == "filipp"
