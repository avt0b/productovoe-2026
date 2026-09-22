import pytest
from conftest import auth_header

import services.storage as storage_module


class FakeS3Client:
    """Подменяет boto3/MinIO в тестах: без сети, хранит объекты в памяти."""

    def __init__(self):
        self.objects: dict[str, bytes] = {}
        self.policies: dict[str, str] = {}
        self.buckets: set[str] = set()

    def head_bucket(self, Bucket):
        if Bucket not in self.buckets:
            from botocore.exceptions import ClientError

            raise ClientError({"Error": {"Code": "404"}}, "HeadBucket")

    def create_bucket(self, Bucket):
        self.buckets.add(Bucket)

    def put_bucket_policy(self, Bucket, Policy):
        self.policies[Bucket] = Policy

    def put_object(self, Bucket, Key, Body, ContentType):
        self.objects[f"{Bucket}/{Key}"] = Body


@pytest.fixture()
def fake_storage(monkeypatch):
    client = FakeS3Client()
    monkeypatch.setattr(storage_module, "_client", client)
    monkeypatch.setattr(storage_module, "_bucket_ready", False)
    monkeypatch.setattr(storage_module, "_get_client", lambda: client)
    yield client


def test_upload_rejects_wrong_content_type(client, fake_storage):
    r = client.post(
        "/uploads",
        headers=auth_header(user_id="u1"),
        files={"file": ("doc.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert r.status_code == 415


def test_upload_rejects_oversized_file(client, fake_storage, monkeypatch):
    monkeypatch.setattr("api.routers.uploads.MAX_UPLOAD_BYTES", 10)
    r = client.post(
        "/uploads",
        headers=auth_header(user_id="u1"),
        files={"file": ("photo.jpg", b"x" * 50, "image/jpeg")},
    )
    assert r.status_code == 413


def test_upload_requires_auth(client, fake_storage):
    r = client.post("/uploads", files={"file": ("photo.jpg", b"abc", "image/jpeg")})
    assert r.status_code in (401, 403)


def test_upload_stores_object_and_returns_url(client, fake_storage):
    r = client.post(
        "/uploads",
        headers=auth_header(user_id="u1"),
        files={"file": ("photo.jpg", b"jpeg-bytes", "image/jpeg")},
    )
    assert r.status_code == 200
    url = r.json()["url"]
    assert url.startswith("http")
    assert url.endswith(".jpg")
    assert "u1/" in url
    assert len(fake_storage.objects) == 1
    assert next(iter(fake_storage.objects.values())) == b"jpeg-bytes"


def test_upload_accepts_audio(client, fake_storage):
    r = client.post(
        "/uploads",
        headers=auth_header(user_id="u1"),
        files={"file": ("memory.mp3", b"id3-bytes", "audio/mpeg")},
    )
    assert r.status_code == 200
    url = r.json()["url"]
    assert url.endswith(".mp3")
    assert "u1/" in url


def test_upload_returns_503_when_storage_down(client, fake_storage):
    from botocore.exceptions import EndpointConnectionError

    def boom(Bucket):
        raise EndpointConnectionError(endpoint_url="http://minio:9000")

    fake_storage.head_bucket = boom
    fake_storage.create_bucket = boom

    r = client.post(
        "/uploads",
        headers=auth_header(user_id="u1"),
        files={"file": ("photo.jpg", b"abc", "image/jpeg")},
    )
    assert r.status_code == 503
