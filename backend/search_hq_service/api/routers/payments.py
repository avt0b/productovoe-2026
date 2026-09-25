from fastapi import APIRouter, Request

from api.deps import NeedServiceDep

router = APIRouter(prefix="/payments", tags=["payments (ЮKassa)"])


@router.post("/yookassa/webhook")
async def yookassa_webhook(request: Request, service: NeedServiceDep) -> dict:
    """ЮKassa шлёт уведомление о смене статуса платежа. Телу не доверяем — по payment_id
    из него сверяем статус отдельным запросом к API (см. NeedService.confirm_payment)."""
    body = await request.json()
    payment_id = (body.get("object") or {}).get("id")
    if payment_id:
        service.confirm_payment(payment_id)
    return {"status": "ok"}
