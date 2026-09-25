import asyncio
import threading

from conftest import auth_header
from test_chat import make_squad, make_trip

from services.chat_broker import ChatBroker


def test_organizations_by_kind_and_city(client):
    historian = auth_header(role="local_historian")
    searcher = auth_header(role="searcher")

    # Отряд заводит поисковик, музей и школу — ещё и краевед.
    assert (
        client.post("/squads", headers=historian, json={"name": "Отряд", "region": "Орёл"}).status_code
        == 403
    )
    museum = client.post(
        "/squads", headers=historian, json={"name": "Военно-исторический музей", "kind": "museum", "region": "Орёл"}
    )
    assert museum.status_code == 201
    assert museum.json()["kind"] == "museum"
    client.post("/squads", headers=searcher, json={"name": "Высота", "region": "Орёл"})
    client.post("/squads", headers=searcher, json={"name": "Рубеж", "region": "Мценск"})

    orel = client.get("/squads", params={"region": "Орёл"}).json()
    assert {s["name"] for s in orel} == {"Военно-исторический музей", "Высота"}
    museums = client.get("/squads", params={"kind": "museum"}).json()
    assert [s["name"] for s in museums] == ["Военно-исторический музей"]
    # Без вида — это отряд, как было до музеев.
    assert {s["kind"] for s in client.get("/squads", params={"region": "Мценск"}).json()} == {"squad"}


def test_delete_trip_takes_its_chat_along(client, leader_header):
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"])
    client.post(f"/trips/{trip['id']}/messages", headers=leader_header, json={"body": "Сбор в 7:00"})

    assert client.delete(f"/trips/{trip['id']}", headers=auth_header(role="searcher")).status_code == 403
    assert client.delete(f"/trips/{trip['id']}", headers=leader_header).status_code == 204
    assert client.get(f"/trips/{trip['id']}").status_code == 404

    # Выезд с тем же id уже не появится, но и переписка его не должна остаться в базе.
    from core.db import SessionLocal
    from core.models import ChatMessage

    with SessionLocal() as db:
        assert db.query(ChatMessage).filter(ChatMessage.subject_id == trip["id"]).count() == 0


def test_disband_squad_removes_needs_trips_and_chats(client, leader_header):
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"])
    need = client.post(
        f"/squads/{squad['id']}/needs", headers=leader_header, json={"kind": "equipment", "title": "Щупы"}
    ).json()
    client.post(f"/trips/{trip['id']}/messages", headers=leader_header, json={"body": "Кто едет?"})

    assert client.delete(f"/squads/{squad['id']}", headers=leader_header).status_code == 204
    assert client.get(f"/trips/{trip['id']}").status_code == 404
    assert client.get(f"/needs/{need['id']}").status_code == 404

    from core.db import SessionLocal
    from core.models import ChatMessage

    with SessionLocal() as db:
        assert db.query(ChatMessage).filter(ChatMessage.subject_id == trip["id"]).count() == 0


def test_chat_returns_latest_messages_in_order(client, leader_header):
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"])
    for n in range(5):
        client.post(f"/trips/{trip['id']}/messages", headers=leader_header, json={"body": f"№{n}"})

    rows = client.get(f"/trips/{trip['id']}/messages", headers=leader_header, params={"limit": 3}).json()
    # Последние три — а раньше приходили первые, и новые сообщения не показывались.
    assert [row["body"] for row in rows] == ["№2", "№3", "№4"]

    since = rows[-1]["created_at"]
    newer = client.get(f"/trips/{trip['id']}/messages", headers=leader_header, params={"since": since}).json()
    assert "№4" in [row["body"] for row in newer]


def test_stream_is_only_for_members(client, leader_header):
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"])
    assert client.get(f"/trips/{trip['id']}/messages/stream", headers=auth_header()).status_code == 403
    assert client.get(f"/trips/{trip['id']}/messages/stream").status_code == 401


def test_broker_delivers_message_published_from_another_thread():
    broker = ChatBroker()

    async def scenario() -> dict:
        subscription = broker.subscribe(("trip", "t1"))
        # Ручка отправки — синхронная и живёт в пуле потоков, а поток SSE — в цикле событий.
        threading.Thread(target=broker.publish, args=(("trip", "t1"), {"body": "привет"})).start()
        try:
            return await asyncio.wait_for(subscription.queue.get(), 2)
        finally:
            broker.unsubscribe(("trip", "t1"), subscription)

    assert asyncio.run(scenario()) == {"body": "привет"}
    assert broker._subscriptions == {}
