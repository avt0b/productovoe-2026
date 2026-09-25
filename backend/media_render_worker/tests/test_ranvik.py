import base64
import io
import wave

import httpx
import pytest
from PIL import Image

from clients import ranvik
from core.config import settings
from core.exceptions import RenderFailed

API = "https://api.ranvik.test/v1"
VIDEO_URL = "https://cdn.ranvik.test/vid/abc/xyz.mp4"
POLL_URL = f"{API}/videos/generations"


def _photo(width: int, height: int) -> bytes:
    buf = io.BytesIO()
    Image.new("L", (width, height)).save(buf, format="PNG")
    return buf.getvalue()


def _wav(seconds: float, rate: int = 48000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(rate)
        wav_file.writeframes(b"\x01\x00" * int(seconds * rate))
    return buf.getvalue()


def _duration(wav_bytes: bytes) -> float:
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        return wav_file.getnframes() / wav_file.getframerate()


VOICE = _wav(3.0)


def _resp(status: int, *, json=None, content: bytes | None = None) -> httpx.Response:
    return httpx.Response(status, json=json, content=content, request=httpx.Request("GET", API))


@pytest.fixture(autouse=True)
def _setup(monkeypatch):
    monkeypatch.setattr(settings, "ranvik_api_key", "rk_live_test")
    monkeypatch.setattr(settings, "ranvik_api_base", API + "/")
    monkeypatch.setattr(settings, "render_timeout_seconds", 60.0)
    monkeypatch.setattr(settings, "ranvik_dry_run", False)
    monkeypatch.setattr(ranvik.time, "sleep", lambda s: None)


def _script(monkeypatch, *, submit: httpx.Response, gets: dict[str, list]) -> list:
    """Подменяет httpx.post/get: ответы по очереди на каждый URL (исключение в
    списке — бросается), запросы копятся в calls."""
    calls = []

    def post(url, **kw):
        calls.append(("POST", url, kw))
        return submit

    def get(url, **kw):
        calls.append(("GET", url, kw))
        answer = gets[url].pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(ranvik.httpx, "post", post)
    monkeypatch.setattr(ranvik.httpx, "get", get)
    return calls


def _animate(photo: bytes | None = None) -> bytes:
    return ranvik.animate(photo=photo or _photo(467, 709), voice_wav=VOICE)


def test_happy_path(monkeypatch):
    calls = _script(
        monkeypatch,
        submit=_resp(202, json={"id": "task_v1", "status": "processing", "object": "video.task"}),
        gets={
            POLL_URL: [
                _resp(200, json={"id": "task_v1", "status": "processing"}),
                # Так видеомодели отвечают на самом деле: список `urls`, а не `url`.
                _resp(200, json={"id": "task_v1", "status": "completed", "urls": [VIDEO_URL]}),
            ],
            VIDEO_URL: [_resp(200, content=b"MP4")],
        },
    )

    assert _animate() == b"MP4"

    _, url, kw = calls[0]
    assert url == f"{API}/videos/generations"
    assert kw["headers"] == {"Authorization": "Bearer rk_live_test"}
    body = kw["json"]
    assert body["model"] == settings.ranvik_model
    assert body["positivePrompt"] == settings.avatar_prompt
    assert body["inputs"]["image"].startswith("data:image/jpeg;base64,")
    # Голос нормальной длины уходит как есть.
    assert body["inputs"]["audio"] == "data:audio/wav;base64," + base64.b64encode(VOICE).decode()
    # Опрос — по task_id в query, готовый файл — без ключа API.
    assert calls[1][2]["params"] == {"task_id": "task_v1"}
    assert calls[-1][1] == VIDEO_URL
    assert "headers" not in calls[-1][2]


def test_big_photo_is_shrunk_before_upload(monkeypatch):
    calls = _script(
        monkeypatch,
        submit=_resp(202, json={"id": "task_v1"}),
        gets={
            POLL_URL: [_resp(200, json={"status": "completed", "url": VIDEO_URL})],
            VIDEO_URL: [_resp(200, content=b"MP4")],
        },
    )

    _animate(_photo(4000, 3000))

    data = calls[0][2]["json"]["inputs"]["image"].split(",", 1)[1]
    assert max(Image.open(io.BytesIO(base64.b64decode(data))).size) == 1280


def test_no_money_is_readable_failure(monkeypatch):
    _script(
        monkeypatch,
        submit=_resp(
            402,
            json={"error": {"type": "billing", "message": "Недостаточно средств", "code": "x"}},
        ),
        gets={},
    )

    with pytest.raises(RenderFailed, match="Ranvik 402: Недостаточно средств"):
        _animate()


def test_failed_task_raises_with_error(monkeypatch):
    _script(
        monkeypatch,
        submit=_resp(202, json={"id": "task_v1"}),
        gets={POLL_URL: [_resp(200, json={"status": "failed", "error": "content policy"})]},
    )

    with pytest.raises(RenderFailed, match="content policy"):
        _animate()


def test_completed_without_url_is_failure(monkeypatch):
    _script(
        monkeypatch,
        submit=_resp(202, json={"id": "task_v1"}),
        gets={POLL_URL: [_resp(200, json={"status": "completed"})]},
    )

    with pytest.raises(RenderFailed, match="без ссылки"):
        _animate()


def test_timeout(monkeypatch):
    monkeypatch.setattr(settings, "render_timeout_seconds", -1.0)
    _script(monkeypatch, submit=_resp(202, json={"id": "task_v1"}), gets={})

    with pytest.raises(RenderFailed, match="Превышено время"):
        _animate()


def test_network_blips_after_payment_are_retried(monkeypatch):
    # Так упал уже оплаченный клип на проверке: обрыв при скачивании с CDN.
    calls = _script(
        monkeypatch,
        submit=_resp(202, json={"id": "task_v1"}),
        gets={
            POLL_URL: [
                httpx.ConnectTimeout("blip"),
                _resp(503, json={"error": "upstream"}),
                _resp(200, json={"status": "completed", "urls": [VIDEO_URL]}),
            ],
            VIDEO_URL: [
                httpx.ConnectTimeout("cdn"),
                httpx.ReadTimeout("cdn"),
                _resp(200, content=b"MP4"),
            ],
        },
    )

    assert _animate() == b"MP4"
    assert [c[0] for c in calls].count("POST") == 1  # постановку не повторяем — вторая оплата


def test_undownloadable_video_fails_with_task_id_for_manual_recovery(monkeypatch):
    monkeypatch.setattr(ranvik, "_DOWNLOAD_WINDOW_SECONDS", 0.0)
    _script(
        monkeypatch,
        submit=_resp(202, json={"id": "task_v1"}),
        gets={
            POLL_URL: [_resp(200, json={"status": "completed", "urls": [VIDEO_URL]})],
            VIDEO_URL: [httpx.ConnectTimeout("cdn")],
        },
    )

    with pytest.raises(RenderFailed, match="task_v1.*не скачался") as exc:
        _animate()
    assert VIDEO_URL in str(exc.value)


def test_client_error_on_poll_is_not_retried(monkeypatch):
    _script(
        monkeypatch,
        submit=_resp(202, json={"id": "task_v1"}),
        gets={POLL_URL: [_resp(401, json={"error": {"message": "bad key"}})]},
    )

    with pytest.raises(httpx.HTTPStatusError):
        _animate()


def test_dry_run_returns_stub_without_any_request(monkeypatch):
    monkeypatch.setattr(settings, "ranvik_dry_run", True)
    calls = _script(monkeypatch, submit=_resp(202, json={"id": "task_v1"}), gets={})

    video = _animate()

    assert calls == []
    assert video[4:8] == b"ftyp"  # настоящий mp4 — плеер на фронте его покажет


def test_dry_run_still_rejects_broken_photo(monkeypatch):
    monkeypatch.setattr(settings, "ranvik_dry_run", True)

    with pytest.raises(RenderFailed, match="исходное фото"):
        ranvik.animate(photo=b"not a photo", voice_wav=VOICE)


def test_short_voice_is_padded_to_kling_minimum():
    # «Помни меня.» — ~1.2 сек, а Kling Avatar принимает от 2 сек (иначе 400).
    padded = ranvik.fit_voice(_wav(1.2))
    assert _duration(padded) == pytest.approx(2.2, abs=0.01)


def test_normal_voice_is_left_untouched():
    assert ranvik.fit_voice(VOICE) == VOICE


def test_too_long_voice_is_cut_to_kling_maximum():
    long_voice = _wav(301, rate=8000)
    assert _duration(ranvik.fit_voice(long_voice)) == pytest.approx(300, abs=0.01)


def test_non_wav_voice_fails_before_any_request(monkeypatch):
    calls = _script(monkeypatch, submit=_resp(202, json={"id": "task_v1"}), gets={})

    with pytest.raises(RenderFailed, match="не WAV"):
        ranvik.animate(photo=_photo(467, 709), voice_wav=b"ID3 mp3")
    assert calls == []


def test_not_an_image_fails_before_any_request(monkeypatch):
    calls = _script(monkeypatch, submit=_resp(202, json={"id": "task_v1"}), gets={})

    with pytest.raises(RenderFailed, match="исходное фото"):
        ranvik.animate(photo=b"<html>not a photo</html>", voice_wav=VOICE)
    assert calls == []
