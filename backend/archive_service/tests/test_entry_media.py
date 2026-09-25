"""Фото и аудиовоспоминание у одной записи (модуль 6 ТЗ)."""

from conftest import auth_header
from sqlalchemy import create_engine, inspect, text

from core.db import ensure_added_columns

PHOTO = "https://marshrutpobedy.website/storage/media/u1/a.jpg"
AUDIO = "https://marshrutpobedy.website/storage/media/u1/b.mp3"


def create_memory(client, header, **over):
    body = {"kind": "memory", "title": "Воспоминания бабушки о 1942-м", "body": "Рассказ очевидца."}
    body.update(over)
    return client.post("/entries", headers=header, json=body)


def test_entry_carries_photo_and_audio_together(client):
    author = auth_header(user_id="author-1")
    r = create_memory(client, author, media_url=PHOTO, audio_url=AUDIO)
    assert r.status_code == 201
    created = r.json()
    assert created["media_url"] == PHOTO
    assert created["audio_url"] == AUDIO

    client.post(
        f"/entries/{created['id']}/verify", headers=auth_header(role="local_historian"), json={}
    )
    [public] = client.get("/entries").json()
    assert public["media_url"] == PHOTO
    assert public["audio_url"] == AUDIO
    assert client.get(f"/entries/{created['id']}").json()["audio_url"] == AUDIO


def test_audio_is_optional(client):
    created = create_memory(client, auth_header()).json()
    assert created["media_url"] is None
    assert created["audio_url"] is None


def test_author_can_attach_and_remove_audio_while_pending(client):
    author = auth_header(user_id="author-1")
    entry = create_memory(client, author, media_url=PHOTO).json()

    added = client.patch(f"/entries/{entry['id']}", headers=author, json={"audio_url": AUDIO}).json()
    assert added["audio_url"] == AUDIO
    assert added["media_url"] == PHOTO  # фото не трогаем

    removed = client.patch(f"/entries/{entry['id']}", headers=author, json={"audio_url": None}).json()
    assert removed["audio_url"] is None
    assert removed["media_url"] == PHOTO


def test_audio_url_length_is_limited(client):
    r = create_memory(client, auth_header(), audio_url="https://x/" + "a" * 500)
    assert r.status_code == 422


def test_audio_url_column_is_added_to_existing_table(tmp_path):
    """Живая БД создана до появления audio_url: create_all её не тронет,
    колонку должен досоздать init_db."""
    old = create_engine(f"sqlite+pysqlite:///{(tmp_path / 'old.sqlite').as_posix()}")
    with old.begin() as conn:
        conn.execute(text("CREATE TABLE archive_entries (id VARCHAR(36) PRIMARY KEY, media_url VARCHAR(500))"))
        conn.execute(text("INSERT INTO archive_entries (id, media_url) VALUES ('e1', 'photo.jpg')"))

    ensure_added_columns(old)
    ensure_added_columns(old)  # повторный старт ничего не ломает

    columns = {c["name"] for c in inspect(old).get_columns("archive_entries")}
    assert "audio_url" in columns
    with old.connect() as conn:
        row = conn.execute(text("SELECT media_url, audio_url FROM archive_entries")).one()
    assert tuple(row) == ("photo.jpg", None)
    old.dispose()
