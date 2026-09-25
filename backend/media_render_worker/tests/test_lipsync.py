import httpx
import pytest

from clients import lipsync
from core.config import settings
from core.errors import RenderFailed

API = "https://api.replicate.com/v1"


class Replicate:
    """Поддельный API Replicate: файлы, прогон и опрос его статуса."""

    def __init__(self, statuses=("processing", "succeeded"), create_status=201, error=None):
        self.statuses = list(statuses)
        self.create_status = create_status
        self.error = error
        self.uploads = []
        self.deleted = []
        self.created = None
        self.canceled = False

    def post(self, url, *, headers, timeout, json=None, files=None, data=None):
        assert headers["Authorization"] == "Bearer token"
        assert headers["User-Agent"].startswith("marshruty")
        if url == f"{API}/files":
            name, content, content_type = files["content"]
            self.uploads.append((name, content, content_type, data))
            file_id = f"file-{len(self.uploads)}"
            return httpx.Response(
                201,
                json={"id": file_id, "urls": {"get": f"{API}/files/{file_id}"}},
                request=httpx.Request("POST", url),
            )
        if url == f"{API}/predictions":
            self.created = {"json": json, "headers": headers}
            if self.create_status >= 400:
                return httpx.Response(
                    self.create_status,
                    json={"title": "Insufficient credit", "detail": "You have insufficient credit"},
                    request=httpx.Request("POST", url),
                )
            return httpx.Response(
                201, json=self._prediction("starting"), request=httpx.Request("POST", url)
            )
        if url.endswith("/cancel"):
            self.canceled = True
            return httpx.Response(
                200, json=self._prediction("canceled"), request=httpx.Request("POST", url)
            )
        raise AssertionError(f"неожиданный POST {url}")

    def get(self, url, *, headers, timeout, follow_redirects=False):
        assert url == f"{API}/predictions/p-1"
        return httpx.Response(
            200, json=self._prediction(self.statuses.pop(0)), request=httpx.Request("GET", url)
        )

    def delete(self, url, *, headers, timeout):
        self.deleted.append(url.rsplit("/", 1)[-1])
        return httpx.Response(204, request=httpx.Request("DELETE", url))

    def _prediction(self, status):
        return {
            "id": "p-1",
            "status": status,
            "urls": {"get": f"{API}/predictions/p-1", "cancel": f"{API}/predictions/p-1/cancel"},
            "output": "https://replicate.delivery/out.mp4" if status == "succeeded" else None,
            "error": self.error if status == "failed" else None,
        }


@pytest.fixture
def replicate(monkeypatch):
    def install(**kwargs):
        fake = Replicate(**kwargs)
        monkeypatch.setattr(lipsync.httpx, "post", fake.post)
        monkeypatch.setattr(lipsync.httpx, "get", fake.get)
        monkeypatch.setattr(lipsync.httpx, "delete", fake.delete)
        return fake

    monkeypatch.setattr(settings, "replicate_api_token", "token")
    monkeypatch.setattr(settings, "replicate_model_version", "cjwbw/sadtalker:v1")
    monkeypatch.setattr(settings, "render_timeout_seconds", 900.0)
    monkeypatch.setattr(lipsync, "_POLL_INTERVAL_SECONDS", 0)
    return install


def test_animate_uploads_files_runs_full_frame_and_cleans_up(replicate):
    fake = replicate()

    assert lipsync.animate(photo=b"JPEG", audio_wav=b"WAV") == "https://replicate.delivery/out.mp4"

    assert [(name, content, kind) for name, content, kind, _ in fake.uploads] == [
        ("photo.jpg", b"JPEG", "image/jpeg"),
        ("voice.wav", b"WAV", "audio/wav"),
    ]
    body = fake.created["json"]
    assert body["version"] == "cjwbw/sadtalker:v1"
    assert body["input"]["source_image"] == f"{API}/files/file-1"
    assert body["input"]["driven_audio"] == f"{API}/files/file-2"
    assert body["input"]["preprocess"] == "full"
    assert fake.created["headers"]["Cancel-After"] == "900s"
    assert fake.deleted == ["file-1", "file-2"]


def test_model_error_is_explained_and_files_still_removed(replicate):
    fake = replicate(statuses=("failed",), error="Face not detected in the source image")

    with pytest.raises(RenderFailed, match="не нашлось лица"):
        lipsync.animate(photo=b"JPEG", audio_wav=b"WAV")
    assert fake.deleted == ["file-1", "file-2"]


def test_no_credit_is_explained(replicate):
    replicate(create_status=402)

    with pytest.raises(RenderFailed, match="на счёте нет средств"):
        lipsync.animate(photo=b"JPEG", audio_wav=b"WAV")


def test_timeout_cancels_prediction(replicate, monkeypatch):
    fake = replicate(statuses=("processing",) * 5)
    monkeypatch.setattr(settings, "render_timeout_seconds", -1.0)

    with pytest.raises(RenderFailed, match="не успел"):
        lipsync.animate(photo=b"JPEG", audio_wav=b"WAV")
    assert fake.canceled is True


def test_download_sends_key_only_to_replicate_api(monkeypatch):
    seen = []

    def get(url, *, headers, timeout, follow_redirects):
        seen.append((url, "Authorization" in headers))
        return httpx.Response(200, content=b"MP4", request=httpx.Request("GET", url))

    monkeypatch.setattr(settings, "replicate_api_token", "token")
    monkeypatch.setattr(lipsync.httpx, "get", get)

    assert lipsync.download("https://replicate.delivery/out.mp4") == b"MP4"
    assert lipsync.download(f"{API}/files/out/download") == b"MP4"
    assert seen == [
        ("https://replicate.delivery/out.mp4", False),
        (f"{API}/files/out/download", True),
    ]
