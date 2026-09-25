import httpx
import pytest

import worker
from core.config import settings
from core.errors import RenderFailed

CLIP = {
    "id": "clip-1",
    "narration_text": "Я сделал это, чтобы ты жил.",
    "voice_style": "era_male",
    "source_photo_url": "http://192.168.3.42:9000/media/user-1/photo.jpg",
}


@pytest.fixture(autouse=True)
def no_ranvik_by_default(monkeypatch):
    monkeypatch.setattr(settings, "ranvik_api_key", "")
    monkeypatch.setattr(settings, "render_provider", "auto")


@pytest.fixture
def keys(monkeypatch):
    monkeypatch.setattr(settings, "yandex_api_key", "key")
    monkeypatch.setattr(settings, "yandex_folder_id", "folder")
    monkeypatch.setattr(settings, "replicate_api_token", "token")
    monkeypatch.setattr(settings, "replicate_model_version", "cjwbw/sadtalker:" + "a" * 64)


@pytest.fixture
def outcome(monkeypatch):
    calls = {}
    monkeypatch.setattr(worker.media_service, "claim_next", lambda: dict(CLIP))
    monkeypatch.setattr(
        worker.media_service,
        "mark_ready",
        lambda clip_id, *, video_url: calls.setdefault("ready", (clip_id, video_url)),
    )
    monkeypatch.setattr(
        worker.media_service,
        "mark_failed",
        lambda clip_id, *, error: calls.setdefault("failed", (clip_id, error)),
    )

    def upload(*, clip_id, content):
        calls["uploaded"] = content
        return "https://minio.local/media/rendered/clip-1.mp4"

    monkeypatch.setattr(worker.storage, "upload_video", upload)
    monkeypatch.setattr(worker.storage, "fetch_source", lambda url: b"PHOTO")
    monkeypatch.setattr(worker.photo, "normalize", lambda content, *, max_side: b"JPEG")
    monkeypatch.setattr(worker.speechkit, "synthesize", lambda text, voice: b"WAV-BYTES")
    monkeypatch.setattr(worker.lipsync, "download", lambda url: b"MP4-BYTES")
    return calls


def test_process_one_returns_false_when_queue_empty(monkeypatch):
    monkeypatch.setattr(worker.media_service, "claim_next", lambda: None)
    assert worker.process_one() is False


def test_process_one_happy_path(monkeypatch, keys, outcome):
    seen = {}

    def animate(*, photo, audio_wav):
        seen.update(photo=photo, audio_wav=audio_wav)
        return "https://replicate.delivery/video.mp4"

    monkeypatch.setattr(worker.lipsync, "animate", animate)

    assert worker.process_one() is True
    assert outcome["ready"] == ("clip-1", "https://minio.local/media/rendered/clip-1.mp4")
    assert outcome["uploaded"] == b"MP4-BYTES"
    # В Replicate уходят сами данные, а не ссылка на MinIO в локальной сети.
    assert seen == {"photo": b"JPEG", "audio_wav": b"WAV-BYTES"}


def test_without_keys_explains_instead_of_protocol_error(monkeypatch, outcome):
    monkeypatch.setattr(settings, "yandex_api_key", "")

    def no_calls(*args, **kwargs):
        raise AssertionError("без ключей во внешние сервисы не ходим")

    monkeypatch.setattr(worker.speechkit, "synthesize", no_calls)

    assert worker.process_one() is True
    clip_id, error = outcome["failed"]
    assert clip_id == "clip-1"
    assert "не настроено" in error


def test_process_one_marks_failed_on_render_error(monkeypatch, keys, outcome):
    def boom(**kw):
        raise RenderFailed("модель недоступна")

    monkeypatch.setattr(worker.lipsync, "animate", boom)

    assert worker.process_one() is True
    assert outcome["failed"] == ("clip-1", "модель недоступна")


def test_process_one_marks_failed_on_network_error(monkeypatch, keys, outcome):
    def boom(text, voice):
        raise httpx.ConnectError("no route to host")

    monkeypatch.setattr(worker.speechkit, "synthesize", boom)

    assert worker.process_one() is True
    assert outcome["failed"][0] == "clip-1"
    assert "ConnectError" in outcome["failed"][1]


def test_unexpected_error_still_releases_clip(monkeypatch, keys, outcome):
    def boom(text, voice):
        raise ValueError("что-то совсем неожиданное")

    monkeypatch.setattr(worker.speechkit, "synthesize", boom)

    assert worker.process_one() is True
    assert outcome["failed"] == ("clip-1", "Внутренняя ошибка рендера — попробуйте ещё раз")


def test_render_configured_needs_all_four_keys(monkeypatch, keys):
    assert settings.render_configured is True
    monkeypatch.setattr(settings, "replicate_model_version", "  ")
    assert settings.render_configured is False


def test_voice_style_falls_back_to_neutral_for_unknown_code():
    from clients.speechkit import VOICE_BY_STYLE

    assert VOICE_BY_STYLE.get("something-unexpected", "filipp") == "filipp"


def test_with_ranvik_key_photo_is_animated_silently(monkeypatch, outcome):
    monkeypatch.setattr(settings, "ranvik_api_key", "rk_live_test")
    seen = {}

    def animate(*, photo):
        seen["photo"] = photo
        return b"SILENT-MP4"

    def no_voice(*args, **kwargs):
        raise AssertionError("беззвучному оживлению голос не нужен")

    monkeypatch.setattr(worker.ranvik, "animate", animate)
    monkeypatch.setattr(worker.speechkit, "synthesize", no_voice)

    assert worker.process_one() is True
    assert outcome["uploaded"] == b"SILENT-MP4"
    assert outcome["ready"][0] == "clip-1"
    assert seen == {"photo": b"JPEG"}


def test_forced_replicate_ignores_ranvik_key(monkeypatch, keys, outcome):
    monkeypatch.setattr(settings, "ranvik_api_key", "rk_live_test")
    monkeypatch.setattr(settings, "render_provider", "replicate")
    monkeypatch.setattr(worker.lipsync, "animate", lambda **kw: "https://replicate.delivery/v.mp4")

    def no_ranvik(**kwargs):
        raise AssertionError("провайдер задан явно — Replicate")

    monkeypatch.setattr(worker.ranvik, "animate", no_ranvik)

    assert worker.process_one() is True
    assert outcome["uploaded"] == b"MP4-BYTES"


def test_provider_choice(monkeypatch, keys):
    assert settings.effective_render_provider == "replicate"
    monkeypatch.setattr(settings, "ranvik_api_key", "rk_live_test")
    assert settings.effective_render_provider == "ranvik"
    monkeypatch.setattr(settings, "ranvik_api_key", "")
    monkeypatch.setattr(settings, "render_provider", "ranvik")
    assert settings.effective_render_provider is None
