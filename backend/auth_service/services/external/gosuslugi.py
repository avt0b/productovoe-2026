from collections.abc import Mapping

from core.exceptions import ExternalProviderNotConfigured
from core.models import ExternalProvider
from services.external.base import AuthorizeRequest, ExternalProfile, ProviderClient


class GosuslugiProvider(ProviderClient):
    """Госуслуги (ЕСИА) — пока заготовка.

    ЕСИА работает по OAuth 2.0 / OpenID Connect, но подключиться к ней может
    только информационная система юрлица, зарегистрированная в ЕСИА: с учётной
    записью организации на Госуслугах, ключом и сертификатом, запросами,
    подписанными по ГОСТ, и проверкой в тестовой среде до выхода в продуктив.
    Пока системы нет, провайдер выключен и ручки отвечают 503.

    Когда регистрация будет, здесь появятся `authorize_url` и `exchange` по
    регламенту ЕСИА (подпись client_secret, обмен кода, данные из ID-токена).
    Ручки и схема входа в приложении при этом не изменятся.
    """

    provider = ExternalProvider.gosuslugi
    title = "Госуслуги"
    kind = "redirect"

    def is_enabled(self) -> bool:
        return False

    def disabled_reason(self) -> str:
        return (
            "Вход через Госуслуги пока не подключён: нужна регистрация системы в ЕСИА "
            "(юрлицо, ключи и подпись по ГОСТ)"
        )

    def authorize_url(self, request: AuthorizeRequest) -> str:
        raise ExternalProviderNotConfigured(self.disabled_reason())

    def exchange(
        self,
        *,
        code: str,
        code_verifier: str,
        redirect_uri: str,
        state: str,
        params: Mapping[str, str],
    ) -> ExternalProfile:
        raise ExternalProviderNotConfigured(self.disabled_reason())
