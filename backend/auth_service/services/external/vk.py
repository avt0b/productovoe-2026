from collections.abc import Mapping
from urllib.parse import urlencode

import httpx

from core.config import settings
from core.exceptions import ExternalProviderError
from core.models import ExternalProvider
from services.external.base import AuthorizeRequest, ExternalProfile, ProviderClient

TIMEOUT_SECONDS = 10


class VkIdProvider(ProviderClient):
    """VK ID: OAuth 2.1 с PKCE.

    Человек подтверждает вход на странице VK ID, та возвращает его на наш callback
    с `code`, `state` и `device_id`. Код меняем на токен, по токену берём профиль.
    Адреса ручек VK ID вынесены в настройки: сверьте их с документацией id.vk.com,
    когда зарегистрируете приложение и получите `VK_ID_CLIENT_ID`.
    """

    provider = ExternalProvider.vk
    title = "VK ID"
    kind = "redirect"

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        # В тестах сюда подставляется httpx.MockTransport вместо сети.
        self.transport = transport

    def is_enabled(self) -> bool:
        return bool(settings.vk_id_client_id)

    def disabled_reason(self) -> str:
        return "Вход через VK ID не настроен: нужен VK_ID_CLIENT_ID приложения из id.vk.com"

    def authorize_url(self, request: AuthorizeRequest) -> str:
        query = {
            "response_type": "code",
            "client_id": settings.vk_id_client_id,
            "redirect_uri": request.redirect_uri,
            "state": request.state,
            "code_challenge": request.code_challenge,
            "code_challenge_method": "S256",
            "scope": settings.vk_id_scope,
        }
        return f"{settings.vk_id_authorize_url}?{urlencode(query)}"

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
            "client_id": settings.vk_id_client_id,
            "device_id": params.get("device_id", ""),
            "redirect_uri": redirect_uri,
            "state": state,
        }
        if settings.vk_id_client_secret:
            token_request["client_secret"] = settings.vk_id_client_secret

        with httpx.Client(transport=self.transport, timeout=TIMEOUT_SECONDS) as http:
            token = self._post(http, settings.vk_id_token_url, token_request)
            access_token = token.get("access_token")
            if not access_token:
                raise ExternalProviderError("VK ID не выдал токен доступа")
            info = self._post(
                http,
                settings.vk_id_user_info_url,
                {"client_id": settings.vk_id_client_id, "access_token": access_token},
            )

        user = info.get("user") or {}
        subject = str(user.get("user_id") or token.get("user_id") or "")
        if not subject:
            raise ExternalProviderError("VK ID не сообщил, кто вошёл")
        name = " ".join(part for part in (user.get("first_name"), user.get("last_name")) if part)
        return ExternalProfile(
            subject=subject,
            display_name=name,
            email=user.get("email") or None,
            avatar_url=user.get("avatar") or None,
        )

    @staticmethod
    def _post(http: httpx.Client, url: str, data: dict[str, str]) -> dict:
        try:
            response = http.post(url, data=data)
        except httpx.HTTPError as error:
            raise ExternalProviderError("VK ID не отвечает — попробуйте позже") from error
        try:
            body = response.json()
        except ValueError:
            body = {}
        if response.status_code >= 400 or (isinstance(body, dict) and body.get("error")):
            reason = body.get("error_description") or body.get("error") or response.status_code
            raise ExternalProviderError(f"VK ID отказал во входе: {reason}")
        return body if isinstance(body, dict) else {}
