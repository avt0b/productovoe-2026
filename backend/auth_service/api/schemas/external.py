from typing import Literal

from pydantic import BaseModel, Field

from api.schemas.auth import TokenPair
from api.schemas.user import UserOut
from core.models import ExternalProvider


class ProviderOut(BaseModel):
    provider: ExternalProvider
    title: str
    # Показывать ли кнопку: провайдер настроен или разрешён тестовый.
    enabled: bool
    # redirect — открыть authorize_url в браузере; bot — открыть ссылку на бота мессенджера.
    kind: Literal["redirect", "bot"]
    # Тестовый провайдер вместо настоящего (только при EXTERNAL_AUTH_MOCK).
    mock: bool


class ExternalStartIn(BaseModel):
    # Куда вернуть человека после подтверждения: адрес приложения, например
    # marshruty://auth/external. Для redirect-провайдеров обязателен.
    return_to: str | None = Field(default=None, max_length=500)


class ExternalStartOut(BaseModel):
    # Секрет попытки: хранится в приложении, в URL не передаётся.
    login_id: str
    provider: ExternalProvider
    authorize_url: str
    kind: Literal["redirect", "bot"]
    expires_in: int


class ExternalCompleteIn(BaseModel):
    login_id: str = Field(min_length=16, max_length=128)
    # Одноразовый код из возврата провайдера (`?result_code=`). Для входа через бота не нужен.
    result_code: str | None = Field(default=None, max_length=128)


class ExternalCompleteOut(TokenPair):
    user: UserOut
    # Имя от провайдера — чтобы приложение заполнило профиль: в auth_service имён нет.
    display_name: str
    is_new_user: bool


class ExternalPendingOut(BaseModel):
    status: Literal["pending"] = "pending"


class WebhookOut(BaseModel):
    ok: bool = True
    # Обновление было про вход и подтвердило попытку.
    handled: bool
