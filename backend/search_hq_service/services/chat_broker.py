"""Раздача новых сообщений чата открытым потокам (SSE) внутри процесса.

Сервис крутится одним процессом uvicorn, поэтому хватает очередей в памяти:
сообщение, записанное в базу, тут же уходит всем, кто держит поток этого
чата. Второй экземпляр сервиса таких сообщений не увидит — клиент всё равно
догружает пропущенное запросом со `since` после каждого переподключения.

Сообщение пишут синхронные ручки из пула потоков, а потоки SSE живут в
цикле событий, поэтому очередь пополняется через `call_soon_threadsafe`.
"""

import asyncio
import threading
from collections.abc import Hashable

from core.models import ChatMessage
from core.timeutil import as_utc

# Сколько сообщений может ждать медленного читателя. Дальше новые теряются —
# клиент их догрузит запросом со `since`, когда заметит, что отстал.
QUEUE_SIZE = 100


class Subscription:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=QUEUE_SIZE)


class ChatBroker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscriptions: dict[Hashable, set[Subscription]] = {}

    def subscribe(self, key: Hashable) -> Subscription:
        subscription = Subscription(asyncio.get_running_loop())
        with self._lock:
            self._subscriptions.setdefault(key, set()).add(subscription)
        return subscription

    def unsubscribe(self, key: Hashable, subscription: Subscription) -> None:
        with self._lock:
            listeners = self._subscriptions.get(key)
            if listeners is None:
                return
            listeners.discard(subscription)
            if not listeners:
                del self._subscriptions[key]

    def publish(self, key: Hashable, payload: dict) -> None:
        with self._lock:
            listeners = list(self._subscriptions.get(key, ()))
        for subscription in listeners:
            try:
                subscription.loop.call_soon_threadsafe(_offer, subscription.queue, payload)
            except RuntimeError:
                # Цикл уже закрыт: поток оборвался, отписаться не успел.
                self.unsubscribe(key, subscription)


def _offer(queue: asyncio.Queue[dict], payload: dict) -> None:
    if not queue.full():
        queue.put_nowait(payload)


def message_payload(message: ChatMessage) -> dict:
    """То же, что отдаёт ChatMessageOut, — поток и список сообщений не расходятся."""
    return {
        "id": message.id,
        "author_id": message.author_id,
        "body": message.body,
        "created_at": as_utc(message.created_at).isoformat(),
    }


chat_broker = ChatBroker()
