"""Загрузка файлов в MinIO (S3-совместимое хранилище).

Бакет создаётся лениво, при первой загрузке — не при старте приложения: локальная
разработка часто идёт без поднятого MinIO, и сервис не должен падать при старте
только из-за недоступного хранилища. Пока MinIO не поднят, `/uploads` отвечает 503,
остальной сервис работает как обычно.

Хранит исходное фото бойца (`source_photo_url`), а также фото и аудиовоспоминания
к записям «Живой памяти» (archive_service хранит только ссылки). Готовое видео
(`video_url`) пишет внешний воркер (media_render_worker), не эта ручка.

Бакет создаётся с публичной политикой на чтение: файлы отдаются браузеру и воркеру
напрямую, без подписанных ссылок. Для прод-домена с CDN политику можно сузить.
"""

import json
import mimetypes
import threading
import uuid

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from core.config import settings
from core.exceptions import ServiceUnavailable

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


def upload(*, key_prefix: str, filename: str, content: bytes, content_type: str | None) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    key = f"{key_prefix}/{uuid.uuid4().hex}{ext}"
    try:
        client = _get_client()
        _ensure_bucket(client)
        client.put_object(
            Bucket=settings.minio_bucket,
            Key=key,
            Body=content,
            ContentType=content_type
            or mimetypes.guess_type(filename)[0]
            or "application/octet-stream",
        )
    except (BotoCoreError, ClientError) as exc:
        raise ServiceUnavailable(f"Не удалось загрузить файл: {exc.__class__.__name__}")

    base = (settings.minio_public_base_url or settings.minio_endpoint).rstrip("/")
    return f"{base}/{settings.minio_bucket}/{key}"
