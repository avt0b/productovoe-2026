"""Загрузка готового ролика в MinIO — тот же бакет, что и у media_service
(`media`), тот же паттерн ленивого создания бакета (services/storage.py там)."""

import json
import mimetypes
import threading
import uuid

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from core.config import settings

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
        raise RuntimeError(f"Не удалось загрузить видео в MinIO: {exc.__class__.__name__}") from exc

    base = (settings.minio_public_base_url or settings.minio_endpoint).rstrip("/")
    return f"{base}/{settings.minio_bucket}/{key}"
