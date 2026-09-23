from core.db import SessionLocal
from scripts.seed_orel import NEEDS, SEED_LEADER, SQUADS, TRIPS, seed, seed_id


def test_seed_is_idempotent(client):
    with SessionLocal() as db:
        first = seed(db)
        second = seed(db)

    assert first == second == {"squads": len(SQUADS), "needs": len(NEEDS), "trips": len(TRIPS)}
    assert len(client.get("/squads").json()) == len(SQUADS)
    assert len(client.get("/trips").json()) == len(TRIPS)


def test_seed_is_marked_demo_and_consistent(client):
    with SessionLocal() as db:
        seed(db)

    squads = client.get("/squads").json()
    assert all(s["leader_id"] == SEED_LEADER for s in squads)
    assert all("ДЕМО" in s["description"] for s in squads)

    # Собрано ровно столько, сколько демо-взносов в ленте сбора.
    need_id = seed_id("need", "vysota-fuel")
    need = client.get(f"/needs/{need_id}").json()
    donations = client.get(f"/needs/{need_id}/donations").json()
    assert need["collected_amount"] == sum(d["amount"] for d in donations) > 0
    assert need["status"] == "open"

    # Выезды считаются от дня запуска — всегда предстоящие.
    assert {t["id"] for t in client.get("/trips", params={"upcoming_only": True}).json()} == {
        seed_id("trip", item.key) for item in TRIPS
    }
