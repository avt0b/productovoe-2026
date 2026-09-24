from html import escape
from typing import Annotated, Any

from fastapi import APIRouter, Body, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from api.deps import ExternalAuthServiceDep
from api.schemas.external import (
    ExternalCompleteIn,
    ExternalCompleteOut,
    ExternalPendingOut,
    ExternalStartIn,
    ExternalStartOut,
    ProviderOut,
    WebhookOut,
)
from api.schemas.user import UserOut
from core.config import settings
from core.exceptions import AppError
from core.models import ExternalProvider
from services.external.registry import REAL_PROVIDERS, mock_allowed

router = APIRouter(prefix="/auth/external", tags=["auth: VK ID, Яндекс ID, MAX, Госуслуги"])


def _page(title: str, text: str, status_code: int = 200, body: str = "") -> HTMLResponse:
    """Простая страница для браузера: callback открывает человек, а не приложение."""
    html = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
</head>
<body style="font-family: system-ui, sans-serif; max-width: 28rem; margin: 10vh auto; padding: 0 1rem">
<h1 style="font-size: 1.4rem">{escape(title)}</h1>
<p>{escape(text)}</p>
{body}
</body>
</html>"""
    return HTMLResponse(html, status_code=status_code)


@router.get("/providers", response_model=list[ProviderOut], summary="Какие способы входа доступны")
def list_providers(service: ExternalAuthServiceDep) -> list[ProviderOut]:
    return [ProviderOut(**info.__dict__) for info in service.providers()]


@router.post(
    "/{provider}/start",
    response_model=ExternalStartOut,
    status_code=status.HTTP_201_CREATED,
    summary="Начать вход: login_id и ссылка для подтверждения",
)
def start_login(
    provider: ExternalProvider,
    service: ExternalAuthServiceDep,
    payload: Annotated[ExternalStartIn | None, Body()] = None,
) -> ExternalStartOut:
    started = service.start(provider, payload.return_to if payload else None)
    return ExternalStartOut(**started.__dict__)


@router.get(
    "/{provider}/callback",
    response_class=RedirectResponse,
    status_code=status.HTTP_303_SEE_OTHER,
    summary="Возврат от VK ID, Яндекс ID или Госуслуг",
)
def provider_callback(provider: ExternalProvider, request: Request, service: ExternalAuthServiceDep):
    try:
        location = service.handle_callback(provider, dict(request.query_params))
    except AppError as error:
        # Сюда приходит человек в браузере — отвечаем страницей, а не JSON.
        return _page("Вход не удался", error.detail, status_code=error.status_code)
    return RedirectResponse(location, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/max/webhook", response_model=WebhookOut, summary="Webhook бота MAX")
def max_webhook(
    request: Request,
    service: ExternalAuthServiceDep,
    update: Annotated[dict[str, Any], Body()],
) -> WebhookOut:
    secret = request.headers.get(settings.max_webhook_secret_header)
    handled = service.handle_bot_update(ExternalProvider.max, secret, update)
    return WebhookOut(handled=handled)


@router.post(
    "/complete",
    response_model=ExternalCompleteOut,
    responses={
        status.HTTP_202_ACCEPTED: {"model": ExternalPendingOut, "description": "Вход ещё не подтверждён"}
    },
    summary="Забрать токены по подтверждённому входу",
)
def complete_login(payload: ExternalCompleteIn, service: ExternalAuthServiceDep):
    completed = service.complete(payload.login_id, payload.result_code)
    if completed is None:
        return JSONResponse(ExternalPendingOut().model_dump(), status_code=status.HTTP_202_ACCEPTED)
    return ExternalCompleteOut(
        access_token=completed.tokens.access_token,
        refresh_token=completed.tokens.refresh_token,
        expires_in=completed.tokens.expires_in,
        user=UserOut.model_validate(completed.user),
        display_name=completed.display_name,
        is_new_user=completed.is_new_user,
    )


@router.get(
    "/mock/authorize",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def mock_authorize(
    provider: Annotated[ExternalProvider, Query()],
    state: Annotated[str, Query(max_length=128)],
) -> HTMLResponse:
    """Страница тестового провайдера: «Войти как тестовый пользователь»."""
    if not mock_allowed():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    title = REAL_PROVIDERS[provider].title
    callback = f"/auth/external/{provider.value}/callback"
    form = f"""<form method="get" action="{escape(callback)}">
<input type="hidden" name="state" value="{escape(state)}">
<input type="hidden" name="code" value="mock">
<p><label>Имя тестового пользователя<br>
<input name="mock_name" value="Тестовый пользователь {escape(title)}" style="width: 100%; padding: .5rem"></label></p>
<p><button type="submit" style="padding: .6rem 1.2rem">Войти</button>
<button type="submit" name="error" value="access_denied" style="padding: .6rem 1.2rem">Отказаться</button></p>
</form>"""
    return _page(
        f"Тестовый вход через {title}",
        f"Это заглушка для локальной разработки: настоящий {title} не вызывается.",
        body=form,
    )
