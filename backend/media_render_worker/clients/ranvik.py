"""Беззвучное оживление фото через Ranvik — агрегатор нейросетей с оплатой в рублях.

Модель по умолчанию — Seedance 1.5 Pro (image-to-video): несколько секунд, в
которые боец на снимке моргает, дышит, чуть улыбается и поворачивает голову.
Звук модели выключаем — голос с липсинком остаётся за SpeechKit + Replicate.

Фото уходит прямо в запросе (`data:` URI): публичная ссылка на MinIO не нужна,
работает и на стенде в локальной сети. Готовый ролик Ranvik хранит на CDN
сутки — воркер скачивает его сразу.

Документация — https://api.ranvik.ru/docs/video."""

import base64
import io
import time
from typing import Any

import httpx
from PIL import Image

from core.config import settings
from core.errors import RenderFailed, raise_for_status

_USER_AGENT = "marshruty-media-render-worker/0.1"
_POLL_INTERVAL_SECONDS = 3.0
_DONE = {"completed", "succeeded", "success"}
_FAILED = {"failed", "error", "canceled", "cancelled"}
# Стороны кадра, которые понимают видеомодели; берём ближайшую к фото.
_ASPECTS = {"16:9": 16 / 9, "4:3": 4 / 3, "1:1": 1.0, "3:4": 3 / 4, "9:16": 9 / 16}

# По-английски модели понимают точнее. Главное — не менять лицо и сам снимок:
# это чужой прадед на фото, а не материал для фантазии модели.
PROMPT = (
    "The person in this old archival portrait photograph comes alive for a few seconds: "
    "a slow natural blink, gentle breathing, a slight warm smile and a small turn of the head. "
    "Subtle, calm and respectful movement. Static camera, same framing. Keep the face, "
    "uniform, clothing and the look of the old photograph (black-and-white or sepia, grain, "
    "scratches) exactly as they are. No text, no new objects or people."
)


def animate(*, photo: bytes) -> bytes:
    """Фото (JPEG) -> MP4 на `RANVIK_DURATION_SECONDS` секунд без звука."""
    task = _create(photo)
    deadline = time.monotonic() + settings.render_timeout_seconds
    while True:
        status = str(task.get("status") or "").lower()
        if status in _DONE:
            return _download(_result_url(task))
        if status in _FAILED:
            raise RenderFailed(_explain(task))
        if time.monotonic() > deadline:
            raise RenderFailed("Ranvik не успел оживить фото — попробуйте ещё раз")
        time.sleep(_POLL_INTERVAL_SECONDS)
        task = _poll(task["id"])


def aspect_ratio(photo: bytes) -> str:
    width, height = Image.open(io.BytesIO(photo)).size
    ratio = width / height
    return min(_ASPECTS, key=lambda name: abs(_ASPECTS[name] - ratio))


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.ranvik_api_key}",
        "User-Agent": _USER_AGENT,
    }


def _create(photo: bytes) -> dict[str, Any]:
    response = httpx.post(
        f"{settings.ranvik_api_base}/videos/generations",
        headers=_headers(),
        json={
            "model": settings.ranvik_model,
            "prompt": PROMPT,
            "image": "data:image/jpeg;base64," + base64.b64encode(photo).decode(),
            "duration": settings.ranvik_duration_seconds,
            "aspectRatio": aspect_ratio(photo),
            "resolution": settings.ranvik_resolution,
            # Seedance по умолчанию дописывает звук и двигает камеру — нам не нужно ни то ни другое.
            "providerSettings": {"bytedance": {"audio": False, "cameraFixed": True}},
        },
        timeout=settings.upstream_timeout_seconds,
    )
    raise_for_status(response, "Ranvik")
    task = response.json()
    task["id"] = task.get("id") or task.get("task_id")
    if not task["id"]:
        raise RenderFailed("Ranvik не вернул номер задачи")
    return task


def _poll(task_id: str) -> dict[str, Any]:
    response = httpx.get(
        f"{settings.ranvik_api_base}/videos/generations",
        params={"task_id": task_id},
        headers=_headers(),
        timeout=settings.upstream_timeout_seconds,
    )
    raise_for_status(response, "Ranvik")
    task = response.json()
    task.setdefault("id", task_id)
    return task


def _result_url(task: dict[str, Any]) -> str:
    # В документации Ranvik встречаются оба вида ответа: `url` и `data[0].url`.
    url = task.get("url")
    if not url and isinstance(task.get("data"), list) and task["data"]:
        url = task["data"][0].get("url")
    if not url:
        raise RenderFailed("Ranvik закончил задачу, но не отдал ссылку на ролик")
    return url


def _download(url: str) -> bytes:
    response = httpx.get(
        url,
        headers={"User-Agent": _USER_AGENT},
        timeout=settings.upstream_timeout_seconds,
        follow_redirects=True,
    )
    raise_for_status(response, "Ranvik")
    return response.content


def _explain(task: dict[str, Any]) -> str:
    error = task.get("error")
    text = str(error.get("message") if isinstance(error, dict) else error or "").strip()
    return f"Ranvik не смог оживить фото: {text[:300]}" if text else "Ranvik вернул ошибку рендера"
