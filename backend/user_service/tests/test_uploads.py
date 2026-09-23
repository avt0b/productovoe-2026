import pytest
from conftest import auth_header

import services.storage as storage_module


class FakeS3Client:
    """Подменяет boto3/MinIO в тестах: без сети, хранит объекты в памяти."""

    def __init__(self):
        self.objects: dict[str, bytes] = {}
        self.buckets: set[str] = set()

    def head_bucket(self, Bucket):
        if Bucket not in self.buckets:
            from botocore.exceptions import ClientError

            raise ClientError({"Error": {"Code": "404"}}, "HeadBucket")

    def create_bucket(self, Bucket):
        self.buckets.add(Bucket)

    def put_bucket_policy(self, Bucket, Policy):
        pass

    def put_object(self, Bucket, Key, Body, ContentType):
        self.objects[f"{Bucket}/{Key}"] = Body


@pytest.fixture()
def fake_storage(monkeypatch):
    client = FakeS3Client()
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


def test_upload_requires_auth(client, fake_storage):
    r = client.post("/uploads", files={"file": ("avatar.jpg", b"abc", "image/jpeg")})
    assert r.status_code in (401, 403)


def test_upload_stores_object_and_returns_url_usable_as_avatar(client, fake_storage):
    r = client.post(
        "/uploads",
        headers=auth_header(user_id="u1"),
        files={"file": ("avatar.jpg", b"jpeg-bytes", "image/jpeg")},
    )
    assert r.status_code == 200
    url = r.json()["url"]
    assert url.endswith(".jpg")
    assert next(iter(fake_storage.objects.values())) == b"jpeg-bytes"

    updated = client.put(
        "/profiles/me", headers=auth_header(user_id="u1"), json={"avatar_url": url}
    )
    assert updated.status_code == 200
    assert updated.json()["avatar_url"] == url


def test_avatar_url_can_be_cleared(client):
    header = auth_header(user_id="u1")
    client.put("/profiles/me", headers=header, json={"avatar_url": "https://example.com/a.jpg"})

    cleared = client.put("/profiles/me", headers=header, json={"avatar_url": None})
    assert cleared.status_code == 200
    assert cleared.json()["avatar_url"] is None


def test_other_fields_ignore_explicit_null(client):
    header = auth_header(user_id="u1")
    client.put("/profiles/me", headers=header, json={"city": "Орёл"})

    r = client.put("/profiles/me", headers=header, json={"city": None})
    assert r.status_code == 200
    assert r.json()["city"] == "Орёл"
