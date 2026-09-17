import secrets
from collections.abc import Mapping
from typing import Any

from core.config import settings
from core.models import ExternalProvider
from services.external.base import AuthorizeRequest, ExternalProfile, ProviderClient


class MaxBotProvider(ProviderClient):
    """MAX: вход через бота мессенджера.

    Публичного OAuth «Войти через MAX» для сторонних приложений нет, поэтому вход
    подтверждается в боте. Приложение открывает ссылку на бота со стартовым
    payload = state попытки, человек запускает бота, мессенджер присылает нам
    webhook — по нему попытка считается подтверждённой.

    Бота на платформе MAX публикует только верифицированное российское юрлицо.
    Форма обновления бота и заголовок секрета webhook вынесены в настройки и
    разбираются в `parse_webhook` терпимо: сверьте их с документацией dev.max.ru,
    когда бот появится.

    Ограничение схемы: у бота нет редиректа на устройство, поэтому приложение
    забирает токены по одному login_id. Ссылку на бота нельзя пересылать —
    кто подтвердит вход по чужой ссылке, войдёт в чужое приложение. Живёт
    попытка минуты, но бот должен прямо спрашивать «Войти в Маршруты победы?».
    """

    provider = ExternalProvider.max
    title = "MAX"
    kind = "bot"

    def is_enabled(self) -> bool:
        return bool(settings.max_bot_name and settings.max_webhook_secret)

    def disabled_reason(self) -> str:
        return "Вход через MAX не настроен: нужны бот на платформе MAX и секрет его webhook"

    def authorize_url(self, request: AuthorizeRequest) -> str:
        return settings.max_bot_link_template.format(bot=settings.max_bot_name, payload=request.state)

    def verify_webhook(self, secret: str | None) -> bool:
        expected = settings.max_webhook_secret
        return bool(expected) and secret is not None and secrets.compare_digest(secret, expected)

    def parse_webhook(self, update: Mapping[str, Any]) -> tuple[str, ExternalProfile] | None:
        update_type = update.get("update_type")
        if update_type == "bot_started":
            payload = update.get("payload")
            user = update.get("user") or {}
        elif update_type == "message_created":
            # Запасной вариант: команда «/start <payload>» обычным сообщением.
            message = update.get("message") or {}
            text = str((message.get("body") or {}).get("text") or "").strip()
            if not text.startswith("/start "):
                return None
            payload = text.split(maxsplit=1)[1]
            user = message.get("sender") or {}
        else:
            return None

        subject = user.get("user_id")
        if not payload or subject is None:
            return None
        name = user.get("name") or " ".join(
            part for part in (user.get("first_name"), user.get("last_name")) if part
        )
        return str(payload), ExternalProfile(subject=str(subject), display_name=name or "")
