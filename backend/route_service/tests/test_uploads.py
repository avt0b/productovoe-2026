import pytest
from conftest import auth_header

import services.storage as storage_module


class FakeS3Client:
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


def test_upload_rejects_unknown_type(client, fake_storage):
    r = client.post(
        "/uploads",
        headers=auth_header(user_id="u1", role="local_historian"),
        files={"file": ("doc.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert r.status_code == 415


def test_upload_accepts_audio_for_waypoint(client, fake_storage):
    r = client.post(
        "/uploads",
        headers=auth_header(user_id="u1", role="local_historian"),
        files={"file": ("story.mp3", b"mp3-bytes", "audio/mpeg")},
    )
    assert r.status_code == 200
    assert r.json()["url"].endswith(".mp3")


def test_uploaded_cover_can_be_attached_to_route(client, fake_storage):
    author = auth_header(user_id="author-1", role="local_historian")
    uploaded = client.post(
        "/uploads", headers=author, files={"file": ("cover.jpg", b"jpeg-bytes", "image/jpeg")}
    )
    url = uploaded.json()["url"]

    route = client.post(
        "/routes",
        headers=author,
        json={"title": "Тропа памяти", "mode": "family", "cover_url": url},
    )
    assert route.status_code == 201
    assert route.json()["cover_url"] == url
