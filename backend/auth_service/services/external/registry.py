from core.config import settings
from core.models import ExternalProvider
from services.external.base import ProviderClient
from services.external.gosuslugi import GosuslugiProvider
from services.external.max import MaxBotProvider
from services.external.mock import MockProvider
from services.external.vk import VkIdProvider
from services.external.yandex import YandexIdProvider

vk_provider = VkIdProvider()
yandex_provider = YandexIdProvider()
max_provider = MaxBotProvider()
gosuslugi_provider = GosuslugiProvider()

REAL_PROVIDERS: dict[ExternalProvider, ProviderClient] = {
    ExternalProvider.vk: vk_provider,
    ExternalProvider.yandex: yandex_provider,
    ExternalProvider.max: max_provider,
    ExternalProvider.gosuslugi: gosuslugi_provider,
}


def mock_allowed() -> bool:
    """Тестовые провайдеры — только при явном флаге и никогда в production."""
    return settings.external_auth_mock and settings.app_env.lower() not in {"production", "prod"}


def get_provider(provider: ExternalProvider) -> ProviderClient:
    """Настоящий провайдер, если он настроен; иначе тестовый, если он разрешён."""
    real = REAL_PROVIDERS[provider]
    if real.is_enabled():
        return real
    if mock_allowed():
        return MockProvider(provider, real.title)
    return real
