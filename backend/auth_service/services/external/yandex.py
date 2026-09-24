from collections.abc import Mapping
from urllib.parse import urlencode

import httpx

from core.config import settings
from core.exceptions import ExternalProviderError
from core.models import ExternalProvider
from services.external.base import AuthorizeRequest, ExternalProfile, ProviderClient

TIMEOUT_SECONDS = 10


class YandexIdProvider(ProviderClient):
    """Яндекс ID: OAuth 2.0 с PKCE.

    Человек подтверждает вход на oauth.yandex.ru, тот возвращает его на наш
    callback с `code` и `state`. Код меняем на токен, по токену берём профиль
    с login.yandex.ru. Приложение регистрирует и физлицо — в отличие от MAX и ЕСИА.
    """

    provider = ExternalProvider.yandex
    title = "Яндекс ID"
    kind = "redirect"

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        # В тестах сюда подставляется httpx.MockTransport вместо сети.
        self.transport = transport

    def is_enabled(self) -> bool:
        return bool(settings.yandex_id_client_id and settings.yandex_id_client_secret)

    def disabled_reason(self) -> str:
        return (
            "Вход через Яндекс ID не настроен: нужны YANDEX_ID_CLIENT_ID и "
            "YANDEX_ID_CLIENT_SECRET приложения из oauth.yandex.ru"
        )

    def authorize_url(self, request: AuthorizeRequest) -> str:
        query = {
            "response_type": "code",
            "client_id": settings.yandex_id_client_id,
            "redirect_uri": request.redirect_uri,
            "state": request.state,
            "code_challenge": request.code_challenge,
            "code_challenge_method": "S256",
        }
        if settings.yandex_id_scope:
            query["scope"] = settings.yandex_id_scope
        return f"{settings.yandex_id_authorize_url}?{urlencode(query)}"

    def exchange(
        self,
        *,
        code: str,
        code_verifier: str,
        redirect_uri: str,
        state: str,
        params: Mapping[str, str],
    ) -> ExternalProfile:
        token_request = {
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": code_verifier,
            "client_id": settings.yandex_id_client_id,
            "client_secret": settings.yandex_id_client_secret,
        }

        with httpx.Client(transport=self.transport, timeout=TIMEOUT_SECONDS) as http:
            try:
                token_response = http.post(settings.yandex_id_token_url, data=token_request)
            except httpx.HTTPError as error:
                raise ExternalProviderError("Яндекс ID не отвечает — попробуйте позже") from error
            token = self._json(token_response)
            access_token = token.get("access_token")
            if not access_token:
                raise ExternalProviderError("Яндекс ID не выдал токен доступа")

            try:
                info_response = http.get(
                    settings.yandex_id_user_info_url,
                    params={"format": "json"},
                    headers={"Authorization": f"OAuth {access_token}"},
                )
            except httpx.HTTPError as error:
                raise ExternalProviderError("Яндекс ID не отвечает — попробуйте позже") from error
            info = self._json(info_response)

        subject = str(info.get("id") or "")
        if not subject:
            raise ExternalProviderError("Яндекс ID не сообщил, кто вошёл")
        name = info.get("real_name") or " ".join(
            part for part in (info.get("first_name"), info.get("last_name")) if part
        )
        avatar_id = info.get("default_avatar_id")
        avatar_url = (
            settings.yandex_id_avatar_url_template.format(avatar_id=avatar_id)
            if avatar_id and not info.get("is_avatar_empty")
            else None
        )
        return ExternalProfile(
            subject=subject,
            display_name=name or info.get("display_name") or info.get("login") or "",
            email=info.get("default_email") or None,
            avatar_url=avatar_url,
        )

    @staticmethod
    def _json(response: httpx.Response) -> dict:
        try:
            body = response.json()
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            body = {}
        if response.status_code >= 400 or body.get("error"):
            reason = body.get("error_description") or body.get("error") or response.status_code
            raise ExternalProviderError(f"Яндекс ID отказал во входе: {reason}")
        return body
