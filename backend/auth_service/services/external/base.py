from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from core.models import ExternalProvider

# redirect — человека отправляют на страницу провайдера, тот возвращает его с кодом
# (VK ID, ЕСИА). bot — человек подтверждает вход в боте мессенджера (MAX).
ProviderKind = Literal["redirect", "bot"]


@dataclass(frozen=True)
class ExternalProfile:
    """Кто вошёл — в том виде, в каком это знает провайдер."""

    subject: str
    display_name: str = ""
    email: str | None = None
    avatar_url: str | None = None


@dataclass(frozen=True)
class AuthorizeRequest:
    state: str
    code_challenge: str
    # Наш callback: сюда провайдер вернёт человека.
    redirect_uri: str


class ProviderClient:
    """Провайдер внешнего входа. Сервис входа работает с любым через этот интерфейс."""

    provider: ExternalProvider
    title: str
    kind: ProviderKind = "redirect"
    mock: bool = False

    def is_enabled(self) -> bool:
        raise NotImplementedError

    def disabled_reason(self) -> str:
        return f"Вход через {self.title} не настроен"

    def authorize_url(self, request: AuthorizeRequest) -> str:
        """Куда отправить человека подтверждать вход."""
        raise NotImplementedError

    def exchange(
        self,
        *,
        code: str,
        code_verifier: str,
        redirect_uri: str,
        state: str,
        params: Mapping[str, str],
    ) -> ExternalProfile:
        """Redirect-провайдер: обменять код из callback на данные человека."""
        raise NotImplementedError

    def verify_webhook(self, secret: str | None) -> bool:
        """Bot-провайдер: запрос действительно пришёл от мессенджера."""
        return False

    def parse_webhook(self, update: Mapping[str, Any]) -> tuple[str, ExternalProfile] | None:
        """Bot-провайдер: достать из обновления бота state попытки и человека."""
        return None
