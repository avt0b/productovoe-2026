"""MinIO: чтение фото героя и загрузка готового ролика — тот же бакет, что и у
media_service (`media`), тот же паттерн ленивого создания бакета
(services/storage.py там)."""

import ipaddress
import json
import mimetypes
import threading
import uuid
from urllib.parse import unquote, urlsplit

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from core.config import settings
from core.exceptions import RenderFailed

# Бакеты всех сервисов, а не только `media`: оживляют и фото из народного
# архива, и фото героя из профиля семьи.
_BUCKETS = frozenset({"users", "media", "archive", "routes"})
# Имена, под которыми MinIO виден изнутри докера и с самого компьютера.
_STAND_HOSTS = frozenset({"localhost", "minio"})

_client = None
_client_lock = threading.Lock()
_bucket_ready = False


def _get_client():
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = boto3.client(
                    "s3",
                    endpoint_url=settings.minio_endpoint,
                    aws_access_key_id=settings.minio_access_key,
                    aws_secret_access_key=settings.minio_secret_key,
                    config=Config(signature_version="s3v4"),
                    region_name="us-east-1",
                )
    return _client


def _ensure_bucket(client) -> None:
    global _bucket_ready
    if _bucket_ready:
        return
    try:
        client.head_bucket(Bucket=settings.minio_bucket)
    except ClientError:
        client.create_bucket(Bucket=settings.minio_bucket)
        client.put_bucket_policy(
            Bucket=settings.minio_bucket,
            Policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{settings.minio_bucket}/*"],
                        }
                    ],
                }
            ),
        )
    _bucket_ready = True


def own_object(url: str) -> tuple[str, str] | None:
    """Бакет и ключ, если ссылка ведёт в наш MinIO; чужая ссылка — `None`.

    Наши ссылки бывают трёх видов: через публичный адрес хранилища (в проде —
    `https://<домен>/storage/<бакет>/<ключ>`), напрямую на MinIO
    (`http://minio:9000/...`) и с IP стенда, который с тех пор мог смениться.
    """
    parts = urlsplit(url)
    # С query — подписанная ссылка: пусть её качают как есть.
    if parts.query or not parts.hostname:
        return None
    path = unquote(parts.path)
    public = urlsplit(settings.minio_public_base_url or "")
    if public.hostname and parts.hostname == public.hostname:
        prefix = public.path.rstrip("/")
        if prefix and not path.startswith(prefix + "/"):
            return None
        path = path[len(prefix):]
    elif parts.hostname != urlsplit(settings.minio_endpoint).hostname and not _is_stand_host(parts.hostname):
        return None
    bucket, _, key = path.lstrip("/").partition("/")
    if bucket not in _BUCKETS or not key:
        return None
    return bucket, key


def _is_stand_host(host: str) -> bool:
    if host in _STAND_HOSTS:
        return True
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    return True


def read_object(bucket: str, key: str) -> bytes:
    """Файл из MinIO — по S3 изнутри докер-сети, а не по публичной ссылке.

    Публичная ссылка ведёт на домен, а сервер не всегда может сходить сам к
    себе: у облака NAT без обратной петли, и у домена бывает AAAA-запись на
    чужой адрес. Изнутри сети MinIO доступен всегда.
    """
    try:
        response = _get_client().get_object(Bucket=bucket, Key=key)
        return response["Body"].read()
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"NoSuchKey", "NoSuchBucket", "404"}:
            raise RenderFailed("Фото героя не найдено в хранилище — загрузите его заново") from exc
        raise RenderFailed(f"Хранилище не отдало фото героя: {code or exc.__class__.__name__}") from exc
    except BotoCoreError as exc:
        raise RenderFailed(f"Хранилище недоступно: {exc.__class__.__name__}") from exc


def upload_video(*, clip_id: str, content: bytes) -> str:
    key = f"rendered/{clip_id}/{uuid.uuid4().hex}.mp4"
    client = _get_client()
    try:
        _ensure_bucket(client)
        client.put_object(
            Bucket=settings.minio_bucket,
            Key=key,
            Body=content,
            ContentType=mimetypes.guess_type(key)[0] or "video/mp4",
        )
    except (BotoCoreError, ClientError) as exc:
        # RenderFailed, а не RuntimeError: иначе воркер не отметит клип упавшим,
        # и он навсегда останется в `processing`.
        raise RenderFailed(f"Не удалось сохранить ролик в хранилище: {exc.__class__.__name__}") from exc

    base = (settings.minio_public_base_url or settings.minio_endpoint).rstrip("/")
    return f"{base}/{settings.minio_bucket}/{key}"
