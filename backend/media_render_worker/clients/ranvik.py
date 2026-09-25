"""Оживление фото — Kling AI Avatar 2.0 (`kling-avatar-20`) через шлюз Ranvik
(api.ranvik.ru): российский агрегатор нейросетей, оплата в рублях, без VPN.

Говорящий портрет: фото бойца + голос SpeechKit -> видео, где боец произносит
текст (губы синхронизированы с речью, моргает, двигает головой). Голос уже
внутри ролика, длина ролика = длине голоса.

Асинхронно: POST /v1/videos/generations -> {id, status}, опрос
GET /v1/videos/generations?task_id=... до `completed`, ролик — по `urls[0]`.
На CDN Ranvik ролик живёт сутки, поэтому скачиваем сразу."""

import base64
import io
import logging
import time
import wave
from pathlib import Path

import httpx
from PIL import Image, ImageOps

from core.config import settings
from core.exceptions import RenderFailed

logger = logging.getLogger(__name__)

_DRY_RUN_VIDEO = Path(__file__).resolve().parent.parent / "assets" / "dry_run.mp4"
_POLL_INTERVAL_SECONDS = 5.0
# Размер ролика наследуется из фото — больше не нужно, а data URI с
# 15-мегабайтным исходником мог бы упереться в лимит размера запроса.
_MAX_PHOTO_SIDE = 1280
# В документации явно назван только успешный `completed` — на провал
# реагируем на любой из привычных вариантов.
_FAILED_STATUSES = {"failed", "error", "cancelled", "canceled", "rejected", "expired"}
# Kling Avatar принимает голос длиной только [2, 300] сек — иначе 400 (так
# отвечал шлюз на «Помни меня.» ~1.2 сек). Короткий добиваем тишиной с запасом.
_MIN_VOICE_SECONDS = 2.2
_MAX_VOICE_SECONDS = 300.0
# Сколько пытаться скачать готовый ролик с CDN Ranvik (соединение с ним
# бывает рвётся — на проверке так упал уже оплаченный клип).
_DOWNLOAD_WINDOW_SECONDS = 180.0


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.ranvik_api_key}"}


def animate(*, photo: bytes, voice_wav: bytes) -> bytes:
    """Фото + голос (WAV) -> mp4, где человек с фото произносит этот голос."""
    # Фото и голос готовим и в пробном режиме: так он ловит и их ошибки.
    image_uri = _photo_data_uri(photo)
    voice_wav = fit_voice(voice_wav)
    if settings.ranvik_dry_run:
        logger.warning("RANVIK_DRY_RUN: в Ranvik не ходим, отдаём заглушку")
        return _DRY_RUN_VIDEO.read_bytes()

    base_url = settings.ranvik_api_base.rstrip("/")
    response = httpx.post(
        f"{base_url}/videos/generations",
        headers=_headers(),
        json={
            "model": settings.ranvik_model,
            "positivePrompt": settings.avatar_prompt,
            "numberResults": 1,
            "outputFormat": "MP4",
            "inputs": {
                "image": image_uri,
                # По схеме модели аудио — URL/UUID, но шлюз принимает и data URL:
                # так голос не надо выкладывать в MinIO по публичной ссылке.
                "audio": "data:audio/wav;base64," + base64.b64encode(voice_wav).decode(),
            },
        },
        timeout=settings.upstream_timeout_seconds,
    )
    if response.status_code >= 400:
        # 402 — кончились деньги на балансе, 429 — rate-limit, 502/504 — сбой у вендора.
        raise RenderFailed(f"Ranvik {response.status_code}: {_error_message(response)}")
    task_id = response.json()["id"]
    # С этого момента генерация оплачена. Постановку задачи не повторяем (второй
    # POST — вторая оплата), а вот опрос и скачивание — повторяем при сбоях сети:
    # иначе разовый обрыв валит уже оплаченный клип, а «Повторить» платит заново.
    logger.info("Ranvik: задача %s поставлена", task_id)

    deadline = time.monotonic() + settings.render_timeout_seconds
    while True:
        if time.monotonic() > deadline:
            raise RenderFailed(f"Превышено время ожидания рендера (задача Ranvik {task_id})")
        time.sleep(_POLL_INTERVAL_SECONDS)
        poll = _get_with_retry(
            f"{base_url}/videos/generations",
            deadline=deadline,
            params={"task_id": task_id},
            headers=_headers(),
        )
        task = poll.json()
        status = task.get("status")
        if status == "completed":
            # В документации — `url`, а видеомодели на деле отдают список `urls`.
            video_url = task.get("url") or next(iter(task.get("urls") or []), None)
            if not video_url:
                raise RenderFailed("Ranvik: задача завершена, но без ссылки на ролик")
            break
        if status in _FAILED_STATUSES:
            raise RenderFailed(f"Ranvik: {_describe(task.get('error')) or status}")

    # Без Authorization: это ссылка на готовый файл на CDN, не на API. Своё
    # окно на скачивание — общий дедлайн к этому моменту может почти истечь.
    try:
        video = _get_with_retry(video_url, deadline=time.monotonic() + _DOWNLOAD_WINDOW_SECONDS)
    except httpx.HTTPError as exc:
        raise RenderFailed(
            f"Ролик готов (задача Ranvik {task_id}), но не скачался: {exc.__class__.__name__}. "
            f"Ссылка живёт сутки: {video_url}"
        ) from exc
    return video.content


def _get_with_retry(url: str, *, deadline: float, **kwargs) -> httpx.Response:
    """GET, который переживает сбои сети и 5xx: повторяет с растущей паузой до
    дедлайна. 4xx — ответ по существу, его не повторяем."""
    pause = 2.0
    while True:
        try:
            response = httpx.get(url, timeout=settings.upstream_timeout_seconds, **kwargs)
            if response.status_code < 500:
                response.raise_for_status()
                return response
            failure: Exception = httpx.HTTPStatusError(
                f"HTTP {response.status_code}", request=response.request, response=response
            )
        except httpx.TransportError as exc:
            failure = exc
        if time.monotonic() + pause > deadline:
            raise failure
        logger.warning("Ranvik: %s, повтор через %.0f с", failure.__class__.__name__, pause)
        time.sleep(pause)
        pause = min(pause * 2, 30.0)


def fit_voice(voice_wav: bytes) -> bytes:
    """WAV в допустимую для Kling Avatar длину: короче минимума — тишина в
    конце, длиннее максимума — обрезка (до неё текст режет воркер заранее)."""
    try:
        with wave.open(io.BytesIO(voice_wav), "rb") as src:
            params = src.getparams()
            frames = src.readframes(params.nframes)
    except (wave.Error, EOFError) as exc:
        raise RenderFailed("Голос от SpeechKit — не WAV") from exc

    frame_size = params.sampwidth * params.nchannels
    min_frames = int(_MIN_VOICE_SECONDS * params.framerate)
    max_frames = int(_MAX_VOICE_SECONDS * params.framerate)
    nframes = len(frames) // frame_size
    if min_frames <= nframes <= max_frames:
        return voice_wav
    if nframes < min_frames:
        frames += b"\x00" * (min_frames - nframes) * frame_size
    else:
        frames = frames[: max_frames * frame_size]

    buf = io.BytesIO()
    with wave.open(buf, "wb") as dst:
        dst.setnchannels(params.nchannels)
        dst.setsampwidth(params.sampwidth)
        dst.setframerate(params.framerate)
        dst.writeframes(frames)
    return buf.getvalue()


def _photo_data_uri(photo: bytes) -> str:
    """JPEG data URI не больше _MAX_PHOTO_SIDE по длинной стороне."""
    try:
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(photo))).convert("RGB")
    except (OSError, Image.DecompressionBombError) as exc:
        raise RenderFailed("Не удалось прочитать исходное фото") from exc
    image.thumbnail((_MAX_PHOTO_SIDE, _MAX_PHOTO_SIDE))
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=92)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def _error_message(response: httpx.Response) -> str:
    try:
        return _describe(response.json().get("error")) or response.text[:300]
    except ValueError:
        return response.text[:300]


def _describe(error) -> str:
    """Ошибка бывает объектом {type, message, code} (формат OpenAI) или строкой."""
    if isinstance(error, dict):
        return str(error.get("message") or error.get("code") or error.get("type") or "")
    return str(error or "")
