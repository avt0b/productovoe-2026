"""Тонкий клиент ЮKassa Payments API v3 (https://yookassa.ru/developers/api).

Без shop_id/secret_key в настройках `get_gateway()` возвращает None — донаты
работают как раньше, без шлюза. Задав ключи (тестового магазина или боевые),
включаем реальный платёжный поток: create_payment → pending → вебхук/сверка
статуса через get_payment → succeeded.
"""

import base64
import uuid
from typing import Any

import httpx

from core.config import settings


class YooKassaGateway:
    def __init__(self, shop_id: str, secret_key: str, base_url: str) -> None:
        token = base64.b64encode(f"{shop_id}:{secret_key}".encode()).decode()
        self._headers = {"Authorization": f"Basic {token}"}
        self._base_url = base_url.rstrip("/")

    def create_payment(
        self, *, amount_rub: int, description: str, return_url: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        response = httpx.post(
            f"{self._base_url}/payments",
            headers={**self._headers, "Idempotence-Key": str(uuid.uuid4())},
            json={
                "amount": {"value": f"{amount_rub}.00", "currency": "RUB"},
                "capture": True,
                "confirmation": {"type": "redirect", "return_url": return_url},
                "description": description,
                "metadata": metadata,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    def get_payment(self, payment_id: str) -> dict[str, Any]:
        # Статус берём этим запросом, а не из тела вебхука — вебхук может подделать кто угодно.
        response = httpx.get(
            f"{self._base_url}/payments/{payment_id}", headers=self._headers, timeout=10.0
        )
        response.raise_for_status()
        return response.json()


def gateway_configured() -> bool:
    return bool(settings.yookassa_shop_id and settings.yookassa_secret_key)


def get_gateway() -> YooKassaGateway | None:
    if not gateway_configured():
        return None
    return YooKassaGateway(
        settings.yookassa_shop_id,  # type: ignore[arg-type]
        settings.yookassa_secret_key,  # type: ignore[arg-type]
        settings.yookassa_api_base,
    )
