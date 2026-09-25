import io

import pytest
from PIL import Image

from core.config import settings
from services import photo, storage


def _jpeg(size=(300, 400), exif=None) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, "gray").save(buf, format="JPEG", exif=exif or b"")
    return buf.getvalue()


# --- фото -------------------------------------------------------------------


def test_normalize_applies_exif_rotation():
    exif = Image.Exif()
    exif[0x0112] = 6  # «повернуть на 90°» — так пишет камера телефона при съёмке вертикально
    out = Image.open(io.BytesIO(photo.normalize(_jpeg((400, 300), exif=exif), max_side=2000)))
    assert out.size == (300, 400)


def test_normalize_flattens_transparency_and_limits_size():
    buf = io.BytesIO()
    Image.new("RGBA", (3000, 1000), (0, 0, 0, 0)).save(buf, format="PNG")
    out = Image.open(io.BytesIO(photo.normalize(buf.getvalue(), max_side=768)))
    assert out.format == "JPEG" and out.mode == "RGB"
    assert max(out.size) == 768
    assert out.getpixel((10, 10)) == (255, 255, 255)


def test_normalize_rejects_garbage():
    with pytest.raises(photo.PhotoUnreadable):
        photo.normalize(b"not an image", max_side=768)


# --- исходное фото из MinIO ---------------------------------------------------


def test_own_photo_is_read_by_key_whatever_host_is_in_url(monkeypatch):
    asked = {}

    class Body:
        def read(self):
            return b"FROM-MINIO"

    class Client:
        def get_object(self, *, Bucket, Key):
            asked.update(bucket=Bucket, key=Key)
            return {"Body": Body()}

    def no_http(*args, **kwargs):
        raise AssertionError("своё фото — не по сети")

    monkeypatch.setattr(storage, "_get_client", lambda: Client())
    monkeypatch.setattr(settings, "minio_bucket", "media")
    monkeypatch.setattr(storage.httpx, "get", no_http)

    # В ссылке — старый IP компьютера, фото всё равно находится.
    content = storage.fetch_source("http://192.168.3.42:9000/media/user-1/photo%20one.jpg")
    assert content == b"FROM-MINIO"
    assert asked == {"bucket": "media", "key": "user-1/photo one.jpg"}


def test_foreign_photo_is_downloaded(monkeypatch):
    class Response:
        content = b"FROM-WEB"

        def raise_for_status(self):
            return None

    monkeypatch.setattr(storage.httpx, "get", lambda url, **kwargs: Response())
    assert storage.fetch_source("https://example.org/archive/soldier.jpg") == b"FROM-WEB"
