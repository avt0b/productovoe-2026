"""Ссылки на наши файлы отдаются с текущим адресом хранилища (core/public_url.py)."""

from core.config import settings
from core.public_url import public_url

OLD_BASE = "http://10.129.169.118:9000"
NEW_BASE = "http://10.71.119.118:9000"


def test_stand_links_follow_current_storage_address(monkeypatch):
    monkeypatch.setattr(settings, "minio_public_base_url", NEW_BASE)
    assert public_url(f"{OLD_BASE}/users/u1/a.jpg") == f"{NEW_BASE}/users/u1/a.jpg"
    assert public_url("http://localhost:9000/media/k.jpg") == f"{NEW_BASE}/media/k.jpg"
    assert public_url("http://minio:9000/archive/k.webp") == f"{NEW_BASE}/archive/k.webp"


def test_foreign_signed_and_prod_links_stay_as_is(monkeypatch):
    monkeypatch.setattr(settings, "minio_public_base_url", NEW_BASE)
    for url in (
        "https://avatars.yandex.net/get-yapic/1/islands-200",
        "https://lh3.googleusercontent.com/aida-public/abc",
        # Бакет совпадает, но хост — доменное имя, а не стенд.
        "https://example.org/media/photo.jpg",
        "https://marshrutpobedy.website/storage/media/u1/a.jpg",
        # Подписанная ссылка: подпись завязана на хост.
        f"{OLD_BASE}/users/u1/a.jpg?X-Amz-Signature=abc",
        f"{OLD_BASE}/not-our-bucket/a.jpg",
        None,
        "",
    ):
        assert public_url(url) == url


def test_route_cover_saved_on_old_network_is_served_with_current_address(
    client, author_header, monkeypatch
):
    created = client.post(
        "/routes",
        headers=author_header,
        json={"title": "Тропа памяти", "mode": "family", "cover_url": f"{OLD_BASE}/routes/c.jpg"},
    ).json()

    monkeypatch.setattr(settings, "minio_public_base_url", NEW_BASE)
    route = client.get(f"/routes/{created['id']}", headers=author_header).json()
    assert route["cover_url"] == f"{NEW_BASE}/routes/c.jpg"
