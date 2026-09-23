"""Тонкий клиент FCM HTTP v1 (https://firebase.google.com/docs/cloud-messaging/send-message).

Один и тот же API шлёт и на Android, и на iOS (FCM сам разносит на APNs), и в
браузер (Web Push) — платформа `NotificationDevice.platform` на формат
запроса не влияет, это уже забота самого FCM по типу токена.

Не настроено (нет `FCM_PROJECT_ID`/ключа) — `send()` просто возвращает
`failed`, ничего не роняя: push — не блокирующая зависимость для остальной
логики уведомлений (см. services/push_service.py).
"""

import enum
import json
import logging
import time

import httpx
import jwt

from core.config import settings

logger = logging.getLogger(__name__)

_FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
_DEFAULT_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Кэш OAuth2-токена в памяти процесса — обмен JWT-ассертии на токен
# устроен так, что дёргать его на каждую отправку не нужно, токен живёт час.
_cached_token: str | None = None
_cached_token_expires_at: float = 0.0


class SendResult(enum.Enum):
    ok = "ok"
    failed = "failed"
    # Токен отозван/устарел на стороне FCM — устройство больше не существует,
    # можно (и нужно) удалить его из NotificationDevice.
    token_invalid = "token_invalid"


def is_configured() -> bool:
    return bool(settings.fcm_project_id) and _load_credentials() is not None


def _load_credentials() -> dict | None:
    if settings.fcm_credentials_json:
        try:
            return json.loads(settings.fcm_credentials_json)
        except ValueError:
            logger.warning("FCM_CREDENTIALS_JSON не парсится как JSON")
            return None
    if settings.fcm_credentials_path:
        try:
            with open(settings.fcm_credentials_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError) as exc:
            logger.warning("Не удалось прочитать FCM_CREDENTIALS_PATH: %s", exc)
            return None
    return None


def _access_token() -> str | None:
    global _cached_token, _cached_token_expires_at
    if _cached_token and time.time() < _cached_token_expires_at:
        return _cached_token

    creds = _load_credentials()
    if creds is None:
        return None

    now = int(time.time())
    token_uri = creds.get("token_uri", _DEFAULT_TOKEN_URL)
    assertion = jwt.encode(
        {
            "iss": creds["client_email"],
            "scope": _FCM_SCOPE,
            "aud": token_uri,
            "iat": now,
            "exp": now + 3600,
        },
        creds["private_key"],
        algorithm="RS256",
    )
    try:
        response = httpx.post(
            token_uri,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            },
            timeout=settings.upstream_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        logger.warning("Не удалось получить OAuth2-токен FCM: %s", exc)
        return None

    _cached_token = payload["access_token"]
    # Запас в минуту, чтобы не уйти в запрос токеном, который истечёт прямо во время него.
    _cached_token_expires_at = time.time() + payload.get("expires_in", 3600) - 60
    return _cached_token


def send(*, token: str, title: str, body: str, data: dict[str, str] | None = None) -> SendResult:
    if not settings.fcm_project_id:
        return SendResult.failed
    access_token = _access_token()
    if access_token is None:
        return SendResult.failed

    url = f"https://fcm.googleapis.com/v1/projects/{settings.fcm_project_id}/messages:send"
    message = {
        "message": {
            "token": token,
            "notification": {"title": title, "body": body},
            "data": {k: str(v) for k, v in (data or {}).items()},
        }
    }
    try:
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            json=message,
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        logger.warning("FCM недоступен: %s", exc)
        return SendResult.failed

    if response.status_code == 200:
        return SendResult.ok

    error_code = None
    try:
        details = response.json().get("error", {}).get("details", [])
        error_code = next((d.get("errorCode") for d in details if "errorCode" in d), None)
    except ValueError:
        pass

    if response.status_code == 404 or error_code == "UNREGISTERED":
        return SendResult.token_invalid

    logger.warning("FCM отклонил отправку (%s): %s", response.status_code, response.text)
    return SendResult.failed
