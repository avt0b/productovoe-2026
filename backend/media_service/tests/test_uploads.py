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


def test_upload_rejects_wrong_content_type(client, fake_storage):
    r = client.post(
        "/uploads",
        headers=auth_header(user_id="u1"),
        files={"file": ("doc.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert r.status_code == 415


def test_uploaded_photo_can_be_used_to_create_clip_linked_to_poi(client, fake_storage):
    author = auth_header(user_id="u1")
    uploaded = client.post(
        "/uploads", headers=author, files={"file": ("soldier.jpg", b"jpeg-bytes", "image/jpeg")}
    )
    assert uploaded.status_code == 200
    url = uploaded.json()["url"]

    clip = client.post(
        "/clips",
        headers=author,
        json={
            "source_photo_url": url,
            "consent_memorial_use": True,
            "poi_id": "poi-grave-1",
        },
    )
    assert clip.status_code == 201
    body = clip.json()
    assert body["source_photo_url"] == url
    assert body["poi_id"] == "poi-grave-1"


def test_public_gallery_filters_by_poi(client, fake_storage):
    author = auth_header(user_id="u1")
    for poi_id in ("poi-a", "poi-b", None):
        client.post(
            "/clips",
            headers=author,
            json={
                "source_photo_url": "https://example.com/x.jpg",
                "consent_memorial_use": True,
                "is_public": True,
                **({"poi_id": poi_id} if poi_id else {}),
            },
        )

    # Ничего не в статусе ready, галерея пуста, но фильтр по poi_id не должен падать.
    r = client.get("/clips", params={"poi_id": "poi-a"})
    assert r.status_code == 200
    assert r.json() == []
