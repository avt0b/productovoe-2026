import worker
from core.exceptions import RenderFailed

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

    def upload_video(*, clip_id, content):
        calls["upload"] = (clip_id, content)
        return "https://minio.local/media/rendered/clip-1.mp4"

    monkeypatch.setattr(worker.media_service, "claim_next", lambda: dict(CLIP))
    monkeypatch.setattr(worker.speechkit, "synthesize", lambda text, voice: b"WAV")
    monkeypatch.setattr(worker, "_download", lambda url: b"JPEG:" + url.encode())
    monkeypatch.setattr(
        worker.ranvik, "animate", lambda *, photo, voice_wav: b"MP4:" + photo + b"+" + voice_wav
    )
    monkeypatch.setattr(worker.storage, "upload_video", upload_video)
    monkeypatch.setattr(
        worker.media_service,
        "mark_ready",
        lambda clip_id, *, video_url: calls.setdefault("ready", (clip_id, video_url)),
    )

    assert worker.process_one() is True
    assert calls["upload"] == ("clip-1", b"MP4:JPEG:https://minio.local/media/photo.jpg+WAV")
    assert calls["ready"] == ("clip-1", "https://minio.local/media/rendered/clip-1.mp4")


def test_long_narration_is_cut_before_synthesis(monkeypatch):
    spoken = {}
    long_text = "Первое предложение. " * 40  # ~800 символов
    monkeypatch.setattr(worker.settings, "max_narration_chars", 100)
    monkeypatch.setattr(
        worker.media_service, "claim_next", lambda: dict(CLIP, narration_text=long_text)
    )
    monkeypatch.setattr(
        worker.speechkit, "synthesize", lambda text, voice: spoken.setdefault("text", text) and b""
    )
    monkeypatch.setattr(worker, "_download", lambda url: b"JPEG")
    monkeypatch.setattr(worker.ranvik, "animate", lambda **kw: b"MP4")
    monkeypatch.setattr(worker.storage, "upload_video", lambda **kw: "url")
    monkeypatch.setattr(worker.media_service, "mark_ready", lambda clip_id, *, video_url: None)

    worker.process_one()

    assert len(spoken["text"]) <= 100
    assert spoken["text"].endswith(".")


def test_limit_narration_keeps_short_text_and_cuts_by_sentence():
    assert worker._limit_narration("  Помни меня.  ", 100) == "Помни меня."
    text = "Я сделал это. Чтобы ты жил и видел голубое небо. Помни меня."
    assert worker._limit_narration(text, 30) == "Я сделал это."


def test_limit_narration_without_sentence_end_cuts_by_word():
    text = "очень длинное предложение без единой точки до самого конца"
    cut = worker._limit_narration(text, 25)
    assert cut == "очень длинное предложение…"


def test_process_one_marks_failed_on_render_error(monkeypatch):
    calls = {}

    monkeypatch.setattr(worker.media_service, "claim_next", lambda: dict(CLIP))
    monkeypatch.setattr(worker.speechkit, "synthesize", lambda text, voice: b"WAV-BYTES")
    monkeypatch.setattr(worker, "_download", lambda url: b"JPEG")

    def boom(**kw):
        raise RenderFailed("модель недоступна")

    monkeypatch.setattr(worker.ranvik, "animate", boom)
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
