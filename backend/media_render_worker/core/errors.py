"""Ошибки рендера, текст которых уходит в заявку — автор видит его в приложении."""

import httpx


class RenderFailed(Exception):
    """Рендер не удался; `str(exc)` — объяснение для автора заявки."""


_REASONS = {
    401: "ключ не принят",
    402: "на счёте нет средств",
    403: "доступ запрещён",
    404: "не найдено — проверьте версию модели",
    422: "сервис не принял входные данные",
    429: "слишком много запросов — повторите позже",
}


def raise_for_status(response: httpx.Response, service: str) -> None:
    """Ответ внешнего сервиса с ошибкой -> RenderFailed с его же объяснением.

    Раньше сюда долетало голое имя исключения («LocalProtocolError»), и по
    нему нельзя было понять, что не так: ключ, деньги на счёте или фото."""
    if response.is_success:
        return
    detail = ""
    try:
        body = response.json()
        if isinstance(body, dict):
            detail = body.get("detail") or body.get("error_message") or body.get("title") or ""
    except ValueError:
        detail = response.text
    reason = _REASONS.get(response.status_code, f"ошибка {response.status_code}")
    message = f"{service}: {reason}"
    if str(detail).strip():
        message += f" ({str(detail).strip()})"
    raise RenderFailed(message[:500])
