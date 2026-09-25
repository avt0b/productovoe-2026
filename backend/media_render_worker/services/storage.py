"""MinIO: исходное фото бойца — оттуда, готовый ролик — туда. Тот же бакет,
что и у media_service (`media`), тот же паттерн ленивого создания бакета
(services/storage.py там)."""

import json
import mimetypes
import threading
import uuid
from urllib.parse import unquote, urlsplit

import boto3
import httpx
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from core.config import settings

_client = None
_client_lock = threading.Lock()
_bucket_ready = False


class StorageFailed(RuntimeError):
    """MinIO не отдал фото или не принял ролик."""


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


def upload_video(*, clip_id: str, content: bytes) -> str:
    key = f"rendered/{clip_id}/{uuid.uuid4().hex}.mp4"
    client = _get_client()
    _ensure_bucket(client)
    try:
        client.put_object(
            Bucket=settings.minio_bucket,
            Key=key,
            Body=content,
            ContentType=mimetypes.guess_type(key)[0] or "video/mp4",
        )
    except (BotoCoreError, ClientError) as exc:
        raise StorageFailed(
            f"Не удалось загрузить видео в MinIO: {exc.__class__.__name__}"
        ) from exc

    base = (settings.minio_public_base_url or settings.minio_endpoint).rstrip("/")
    return f"{base}/{settings.minio_bucket}/{key}"


def fetch_source(url: str) -> bytes:
    """Исходное фото по ссылке из заявки.

    Своё фото берём из бакета по ключу, а не по ссылке: в ссылке — публичный
    адрес MinIO на момент загрузки (IP компьютера в сети), он меняется вместе
    с сетью, и изнутри докера до него не достучаться. Чужую ссылку — просто
    скачиваем."""
    prefix = f"/{settings.minio_bucket}/"
    path = unquote(urlsplit(url).path)
    if path.startswith(prefix):
        try:
            obj = _get_client().get_object(Bucket=settings.minio_bucket, Key=path[len(prefix) :])
            return obj["Body"].read()
        except (BotoCoreError, ClientError):
            pass  # Нет в нашем бакете — может, это чужой MinIO с тем же именем бакета.
    try:
        response = httpx.get(url, timeout=settings.upstream_timeout_seconds, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise StorageFailed("Не удалось получить исходное фото — загрузите его заново") from exc
    return response.content
