"""Сквозная проверка «Живого фото» на поднятом стеке — как обычный пользователь:
регистрация -> вход -> загрузка фото -> заявка -> ждём ready/failed -> качаем ролик.

Запускать внутри сети docker compose (там адреса сервисов — по именам), см.
README воркера, «Проверка целиком»:

  docker compose run --rm -v "<фото>:/in/photo.jpg:ro" -v "<папка>:/out" \\
      media_render_worker python scripts/smoke_e2e.py /in/photo.jpg /out

Сколько стоит, решает RANVIK_DRY_RUN у воркера: true — 0 ₽ (заглушка вместо
Ranvik), false — настоящий Kling Avatar, ~5.8 ₽ за секунду речи (фраза по
умолчанию «Помни меня.» — около 1.5 сек)."""

import argparse
import mimetypes
import os
import sys
import time
import uuid
from pathlib import Path

import httpx

AUTH_URL = os.environ.get("SMOKE_AUTH_URL", "http://auth_service:8001")
MEDIA_URL = os.environ.get("SMOKE_MEDIA_URL", "http://media_service:8007")


def _ok(response: httpx.Response, step: str) -> dict:
    if response.status_code >= 400:
        sys.exit(f"✗ {step}: HTTP {response.status_code} {response.text[:300]}")
    print(f"✓ {step}")
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("photo", type=Path, help="фото бойца (jpg/png/webp)")
    parser.add_argument("out_dir", type=Path, help="куда положить готовый ролик")
    parser.add_argument("--text", default="Помни меня.", help="что скажет боец")
    parser.add_argument(
        "--voice", default="era_male", choices=["era_male", "era_female", "neutral"]
    )
    parser.add_argument("--timeout", type=float, default=900, help="сколько ждать ready, сек")
    args = parser.parse_args()

    # Одноразовый пользователь — чтобы не трогать настоящие аккаунты.
    email, password = f"smoke-{uuid.uuid4().hex[:8]}@example.com", uuid.uuid4().hex
    creds = {"email": email, "password": password}
    _ok(httpx.post(f"{AUTH_URL}/auth/register", json=creds, timeout=30), f"регистрация {email}")
    tokens = _ok(httpx.post(f"{AUTH_URL}/auth/login", json=creds, timeout=30), "вход")
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}

    content_type = mimetypes.guess_type(args.photo.name)[0] or "image/jpeg"
    upload = _ok(
        httpx.post(
            f"{MEDIA_URL}/uploads",
            headers=auth,
            files={"file": (args.photo.name, args.photo.read_bytes(), content_type)},
            timeout=60,
        ),
        "загрузка фото",
    )
    print(f"  фото: {upload['url']}")

    clip = _ok(
        httpx.post(
            f"{MEDIA_URL}/clips",
            headers=auth,
            json={
                "soldier_name": "Смоук-тест",
                "source_photo_url": upload["url"],
                "narration_text": args.text,
                "voice_style": args.voice,
                "consent_memorial_use": True,
                "is_public": False,
            },
            timeout=30,
        ),
        "заявка создана",
    )
    print(f"  клип {clip['id']}: {clip['status']}")

    started, last = time.monotonic(), clip["status"]
    while clip["status"] in ("queued", "processing"):
        if time.monotonic() - started > args.timeout:
            sys.exit(f"✗ клип завис в «{clip['status']}» дольше {args.timeout:.0f} сек")
        time.sleep(5)
        clip = httpx.get(f"{MEDIA_URL}/clips/{clip['id']}", headers=auth, timeout=30).json()
        if clip["status"] != last:
            print(f"  {time.monotonic() - started:4.0f} с: {last} -> {clip['status']}")
            last = clip["status"]

    if clip["status"] != "ready":
        sys.exit(f"✗ клип {clip['status']}: {clip['error']}")

    video = httpx.get(clip["video_url"], timeout=120)
    if video.status_code >= 400 or video.content[4:8] != b"ftyp":
        sys.exit(f"✗ ролик по {clip['video_url']} не скачался как mp4 (HTTP {video.status_code})")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"smoke_{clip['id']}.mp4"
    out.write_bytes(video.content)
    print(f"✓ ready за {time.monotonic() - started:.0f} с, ролик {len(video.content) // 1024} КБ")
    print(f"  {clip['video_url']}")
    print(f"  сохранён: {out}")


if __name__ == "__main__":
    main()
