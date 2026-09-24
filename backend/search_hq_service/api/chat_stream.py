"""Поток новых сообщений чата — Server-Sent Events.

Соединение с базой нужно только на проверку доступа: поток открыт, пока открыт
чат, и держать всё это время соединение из пула нельзя — десяток открытых
чатов выбрал бы пул целиком, и сервис встал бы.

nginx по умолчанию копит ответ в буфере — `X-Accel-Buffering: no` просит его
отдавать события сразу, иначе через шлюз «живой» чат приходил бы пачками.
"""

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import Request
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from core.db import SessionLocal
from core.models import ChatSubjectType
from core.security import Principal
from services.chat_broker import chat_broker
from services.chat_service import ChatService

# Раз в столько секунд — пустой комментарий: прокси и телефон не рвут тихое соединение.
HEARTBEAT_SECONDS = 15


async def chat_stream(
    request: Request, principal: Principal, subject_type: ChatSubjectType, subject_id: str
) -> StreamingResponse:
    def check_access() -> None:
        with SessionLocal() as db:
            service = ChatService(db)
            if subject_type is ChatSubjectType.trip:
                service.ensure_trip_access(principal, subject_id)
            else:
                service.ensure_excursion_access(principal, subject_id)

    await run_in_threadpool(check_access)
    key = (subject_type, subject_id)

    async def events() -> AsyncIterator[str]:
        subscription = chat_broker.subscribe(key)
        try:
            # «ready» — подписка уже есть: клиент догружает пропущенное и ничего не теряет.
            yield "retry: 3000\nevent: ready\ndata: {}\n\n"
            while not await request.is_disconnected():
                try:
                    payload = await asyncio.wait_for(subscription.queue.get(), HEARTBEAT_SECONDS)
                except TimeoutError:
                    yield ": ping\n\n"
                    continue
                yield f"event: message\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
        finally:
            chat_broker.unsubscribe(key, subscription)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
