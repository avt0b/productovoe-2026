import hashlib
from collections.abc import Mapping
from urllib.parse import urlencode

from core.config import settings
from core.exceptions import ExternalProviderError
from core.models import ExternalProvider
from services.external.base import AuthorizeRequest, ExternalProfile, ProviderClient


class MockProvider(ProviderClient):
    """Тестовый провайдер для локальной разработки.

    Вместо VK ID, MAX или Госуслуг открывается наша страница «Войти как тестовый
    пользователь». Дальше всё как у настоящего redirect-провайдера: callback,
    одноразовый код, выдача токенов. Так весь вход можно пройти без ключей и
    юрлица. Включается `EXTERNAL_AUTH_MOCK=true` и никогда — в production.
    """

    kind = "redirect"
    mock = True

    def __init__(self, provider: ExternalProvider, title: str) -> None:
        self.provider = provider
        self.title = title

    def is_enabled(self) -> bool:
        return True

    def authorize_url(self, request: AuthorizeRequest) -> str:
        query = urlencode({"provider": self.provider.value, "state": request.state})
        return f"{settings.external_auth_public_url.rstrip('/')}/auth/external/mock/authorize?{query}"

    def exchange(
        self,
        *,
        code: str,
        code_verifier: str,
        redirect_uri: str,
        state: str,
        params: Mapping[str, str],
    ) -> ExternalProfile:
        if code != "mock":
            raise ExternalProviderError("Тестовый провайдер не узнал код входа")
        name = (params.get("mock_name") or "").strip() or f"Тестовый пользователь {self.title}"
        # Одно и то же имя — один и тот же тестовый человек: так проверяется повторный вход.
        subject = "mock-" + hashlib.sha256(name.encode()).hexdigest()[:16]
        return ExternalProfile(subject=subject, display_name=name)
