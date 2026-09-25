"""Адрес файла из нашего MinIO — с сегодняшним публичным адресом хранилища.

В базе ссылка лежит целиком, с `MINIO_PUBLIC_BASE_URL` на момент загрузки. На
стенде это IP компьютера в локальной сети: сменилась сеть — и все загруженные
раньше аватарки, фото, аудио и ролики ведут в никуда. Поэтому наружу ссылку
отдаём пересобранной: тот же бакет и ключ, но хост — текущий. Старые записи
оживают без миграции.

Чужие ссылки (аватарки VK и Яндекса, картинки из макета) не трогаем: их хост —
доменное имя, а не IP стенда. В проде адрес хранилища постоянный, и
пересборка ничего не меняет."""

import ipaddress
from typing import Annotated
from urllib.parse import urlsplit

from pydantic import AfterValidator

from core.config import settings

# Бакеты всех сервисов, а не только своего: запись архива может ссылаться на
# фото, загруженное через media_service, а герой семьи — на фото из архива.
_BUCKETS = frozenset({"users", "media", "archive", "routes"})
# Имена, под которыми MinIO виден изнутри докера и с самого компьютера.
_STAND_HOSTS = frozenset({"localhost", "minio"})


def public_url(url: str | None) -> str | None:
    if not url:
        return url
    parts = urlsplit(url)
    bucket = parts.path.lstrip("/").split("/", 1)[0]
    # С query — подписанная ссылка: подпись завязана на хост, пересобирать нельзя.
    if bucket not in _BUCKETS or parts.query or not _is_stand_host(parts.hostname):
        return url
    base = (settings.minio_public_base_url or settings.minio_endpoint).rstrip("/")
    return f"{base}{parts.path}"


def _is_stand_host(host: str | None) -> bool:
    if not host:
        return False
    if host in _STAND_HOSTS:
        return True
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    return True


# Тип поля в ответе API: ссылка на наш файл уходит с текущим адресом хранилища.
PublicUrl = Annotated[str, AfterValidator(public_url)]
