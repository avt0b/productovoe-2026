import io

import httpx
import pytest
from PIL import Image

from clients import ranvik
from core.config import settings
from core.errors import RenderFailed

API = "https://api.ranvik.ru/v1"
CDN = "https://cdn.ranvik.ru/vid/abc/clip.mp4"


def jpeg(size=(600, 800)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, "gray").save(buf, format="JPEG")
    return buf.getvalue()


class Ranvik:
    """Поддельный Ranvik: создание задачи, опрос статуса, CDN с роликом."""

    def __init__(
        self,
        polls=({"status": "processing"}, {"status": "completed", "url": CDN}),
        create_status=202,
    ):
        self.polls = list(polls)
        self.create_status = create_status
        self.created = None
        self.polled_with = []

    def post(self, url, *, headers, json, timeout):
        assert url == f"{API}/videos/generations"
        assert headers["Authorization"] == "Bearer rk_live_test"
        self.created = json
        if self.create_status >= 400:
            return httpx.Response(
                self.create_status,
                json={"error_message": "Недостаточно средств на балансе"},
                request=httpx.Request("POST", url),
            )
        return httpx.Response(
            202, json={"id": "task_v1", "status": "queued"}, request=httpx.Request("POST", url)
        )

    def get(self, url, *, headers, timeout, params=None, follow_redirects=False):
        if url == CDN:
            return httpx.Response(200, content=b"MP4", request=httpx.Request("GET", url))
        assert url == f"{API}/videos/generations"
        self.polled_with.append(params)
        return httpx.Response(200, json=self.polls.pop(0), request=httpx.Request("GET", url))


@pytest.fixture
def api(monkeypatch):
    def install(**kwargs):
        fake = Ranvik(**kwargs)
        monkeypatch.setattr(ranvik.httpx, "post", fake.post)
        monkeypatch.setattr(ranvik.httpx, "get", fake.get)
        return fake

    monkeypatch.setattr(settings, "ranvik_api_key", "rk_live_test")
    monkeypatch.setattr(settings, "ranvik_api_base", API)
    monkeypatch.setattr(settings, "render_timeout_seconds", 900.0)
    monkeypatch.setattr(ranvik, "_POLL_INTERVAL_SECONDS", 0)
    return install


def test_animates_photo_silently_for_a_few_seconds(api):
    fake = api()

    assert ranvik.animate(photo=jpeg()) == b"MP4"

    body = fake.created
    assert body["model"] == "seedance-15-pro"
    assert body["image"].startswith("data:image/jpeg;base64,")
    assert body["duration"] == 5
    assert body["aspectRatio"] == "3:4"
    assert body["providerSettings"] == {"bytedance": {"audio": False, "cameraFixed": True}}
    assert fake.polled_with == [{"task_id": "task_v1"}, {"task_id": "task_v1"}]


def test_result_url_may_come_in_data_list(api):
    api(polls=({"status": "completed", "data": [{"url": CDN}]},))

    assert ranvik.animate(photo=jpeg()) == b"MP4"


def test_failed_task_is_explained(api):
    api(polls=({"status": "failed", "error": {"message": "face not detected"}},))

    with pytest.raises(RenderFailed, match="Ranvik не смог оживить фото: face not detected"):
        ranvik.animate(photo=jpeg())


def test_empty_balance_is_explained(api):
    api(create_status=402)

    with pytest.raises(RenderFailed, match="Ranvik: на счёте нет средств"):
        ranvik.animate(photo=jpeg())


def test_gives_up_after_render_timeout(api, monkeypatch):
    api(polls=({"status": "processing"},) * 3)
    monkeypatch.setattr(settings, "render_timeout_seconds", -1.0)

    with pytest.raises(RenderFailed, match="не успел"):
        ranvik.animate(photo=jpeg())


@pytest.mark.parametrize(
    ("size", "aspect"),
    [((1600, 900), "16:9"), ((1000, 1000), "1:1"), ((600, 800), "3:4"), ((540, 960), "9:16")],
)
def test_frame_follows_photo_proportions(size, aspect):
    assert ranvik.aspect_ratio(jpeg(size)) == aspect
