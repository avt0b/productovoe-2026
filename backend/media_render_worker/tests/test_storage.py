import pytest

from services import storage


@pytest.fixture(autouse=True)
def prod_minio(monkeypatch):
    monkeypatch.setattr(storage.settings, "minio_endpoint", "http://minio:9000")
    monkeypatch.setattr(storage.settings, "minio_public_base_url", "https://marshrutpobedy.website/storage")


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        # Публичный адрес хранилища в проде — через nginx, с префиксом /storage.
        (
            "https://marshrutpobedy.website/storage/media/4fd1/1879.jpg",
            ("media", "4fd1/1879.jpg"),
        ),
        # Фото из архива и из профиля — другие бакеты того же MinIO.
        ("https://marshrutpobedy.website/storage/archive/e/1.jpg", ("archive", "e/1.jpg")),
        ("https://marshrutpobedy.website/storage/users/u/avatar.png", ("users", "u/avatar.png")),
        # Прямо на MinIO изнутри докера.
        ("http://minio:9000/media/a/b.jpg", ("media", "a/b.jpg")),
        # IP стенда, который с тех пор мог смениться.
        ("http://192.168.3.42:9000/media/a/b.jpg", ("media", "a/b.jpg")),
        # Ключ с процентами в ссылке — в MinIO он лежит раскодированным.
        ("https://marshrutpobedy.website/storage/media/a/%D1%84%D0%BE%D1%82%D0%BE.jpg", ("media", "a/фото.jpg")),
    ],
)
def test_own_object_recognises_our_links(url, expected):
    assert storage.own_object(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        # Чужой сайт.
        "https://upload.wikimedia.org/wikipedia/commons/a/b.jpg",
        # Наш домен, но не хранилище.
        "https://marshrutpobedy.website/media/a/b.jpg",
        # Неизвестный бакет.
        "https://marshrutpobedy.website/storage/secret/a.jpg",
        # Бакет без ключа.
        "https://marshrutpobedy.website/storage/media/",
        # Подписанная ссылка — качается как есть.
        "http://minio:9000/media/a.jpg?X-Amz-Signature=abc",
    ],
)
def test_own_object_ignores_foreign_links(url):
    assert storage.own_object(url) is None


def test_missing_photo_is_a_render_failure(monkeypatch):
    from botocore.exceptions import ClientError

    class Client:
        def get_object(self, **kw):
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")

    monkeypatch.setattr(storage, "_get_client", lambda: Client())

    with pytest.raises(storage.RenderFailed, match="не найдено"):
        storage.read_object("media", "gone.jpg")
