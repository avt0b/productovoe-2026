"""Демо-наполнение «Поискового штаба» по Орловской области: отряды, сборы, выезды.

Запуск из `backend/search_hq_service`:

    uv run python -m scripts.seed_orel

Скрипт идемпотентный: у каждой строки постоянный id (uuid5 от ключа), повторный
запуск обновляет те же строки. Схему создаёт сам — сервис запускать не нужно.

Всё здесь — ДЕМО по сценариям кейса («Командир отряда «Высота» хочет создать
заявку на набор волонтёров», целевые сборы «Поднять бойца», «Экипировать
отряд»). Это не настоящие отряды и не настоящие деньги: в описании каждой
строки стоит «ДЕМО», а взносы заведены без жертвователя. Синтетика жюри
(`mock_teams.json`) заменит этот набор, когда её выдадут.

Даты выездов считаются от дня запуска, чтобы выезды всегда были предстоящими.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from core.models import (
    Donation,
    NeedKind,
    NeedStatus,
    Squad,
    SquadKind,
    SquadNeed,
    VolunteerTrip,
)

# Командир демо-отрядов. Не UUID пользователя — по нему демо легко найти и удалить.
SEED_LEADER = "seed-orel"

# Тот же неймспейс, что у демо-данных map_service и route_service.
SEED_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "marshruty/seed/orel")

DEMO = "ДЕМО-данные для показа, не настоящий отряд."
# У музеев и школ названия узнаваемые, но сведения и связь с ними — выдуманные.
DEMO_ORG = "ДЕМО-данные для показа: связь с организацией выдумана."


def seed_id(kind: str, key: str) -> str:
    return str(uuid.uuid5(SEED_NAMESPACE, f"{kind}:{key}"))


@dataclass(frozen=True)
class SquadSeed:
    key: str
    name: str
    region: str
    description: str
    kind: SquadKind = SquadKind.squad


@dataclass(frozen=True)
class NeedSeed:
    key: str
    squad: str
    kind: NeedKind
    title: str
    description: str
    target_amount: int | None = None
    # Демо-взносы: суммы без жертвователя. Собрано = их сумма.
    donations: tuple[int, ...] = ()


@dataclass(frozen=True)
class TripSeed:
    key: str
    squad: str
    title: str
    location: str
    days_from_now: int
    capacity: int
    description: str
    checklist: str


SQUADS: tuple[SquadSeed, ...] = (
    SquadSeed(
        key="vysota",
        name="Поисковый отряд «Высота»",
        region="Орёл",
        description=f"Ищет места гибели десантников 5-го ВДК под Орлом. {DEMO}",
    ),
    SquadSeed(
        key="rubezh",
        name="Поисковый отряд «Рубеж»",
        region="Мценск",
        description=f"Работает на рубежах обороны 1941 года по реке Зуше. {DEMO}",
    ),
    SquadSeed(
        key="bolkhov",
        name="Поисковый отряд «Болховский плацдарм»",
        region="Болхов",
        description=f"Экспедиции в леса Болховского района. {DEMO}",
    ),
    # Музеи и школы — к ним краеведы и поисковики относят себя в заявке на роль.
    SquadSeed(
        key="museum-military-history",
        name="Орловский военно-исторический музей",
        region="Орёл",
        description=f"Экспозиция о битве на Орловской дуге и освобождении Орла. {DEMO_ORG}",
        kind=SquadKind.museum,
    ),
    SquadSeed(
        key="museum-diorama",
        name="Музей-диорама «Орловская наступательная операция»",
        region="Орёл",
        description=f"Диорама боёв за Орёл летом 1943 года. {DEMO_ORG}",
        kind=SquadKind.museum,
    ),
    SquadSeed(
        key="museum-local-lore",
        name="Орловский краеведческий музей",
        region="Орёл",
        description=f"Фонды по истории края, в том числе по годам оккупации. {DEMO_ORG}",
        kind=SquadKind.museum,
    ),
    SquadSeed(
        key="museum-mtsensk",
        name="Мценский краеведческий музей",
        region="Мценск",
        description=f"Рубежи обороны 1941 года по реке Зуше. {DEMO_ORG}",
        kind=SquadKind.museum,
    ),
    SquadSeed(
        key="school-orel-pamyat",
        name="Поисковый клуб «Память» при школе № 26",
        region="Орёл",
        description=f"Школьники ведут «Книгу памяти» своего района. {DEMO_ORG}",
        kind=SquadKind.school,
    ),
    SquadSeed(
        key="school-orel-lyceum",
        name="Краеведческий кружок лицея № 1",
        region="Орёл",
        description=f"Исследовательские работы о земляках-фронтовиках. {DEMO_ORG}",
        kind=SquadKind.school,
    ),
    SquadSeed(
        key="school-mtsensk",
        name="Военно-патриотический клуб «Рубеж» при школе № 7",
        region="Мценск",
        description=f"Вахты памяти вместе с поисковиками. {DEMO_ORG}",
        kind=SquadKind.school,
    ),
)

NEEDS: tuple[NeedSeed, ...] = (
    NeedSeed(
        key="vysota-fuel",
        squad="vysota",
        kind=NeedKind.funds,
        title="Поднять бойца: ГСМ и генератор",
        description=(
            "Бензин для мотопомп и дизельный генератор для весенней экспедиции "
            f"в глухие леса Болховского района. {DEMO}"
        ),
        target_amount=50_000,
        donations=(15_000, 12_000, 8_000),
    ),
    NeedSeed(
        key="rubezh-gear",
        squad="rubezh",
        kind=NeedKind.funds,
        title="Экипировать отряд: металлоискатели и щупы",
        description=f"Два металлоискателя и комплект щупов для новичков полевой школы. {DEMO}",
        target_amount=120_000,
        donations=(30_000, 12_000),
    ),
    NeedSeed(
        key="vysota-people",
        squad="vysota",
        kind=NeedKind.volunteers,
        title="Нужны люди на раскопки",
        description=f"10 человек на выходные: копать, просеивать грунт, вести полевой журнал. {DEMO}",
    ),
    NeedSeed(
        key="bolkhov-tents",
        squad="bolkhov",
        kind=NeedKind.equipment,
        title="Палатки и спальники",
        description=f"Три палатки на 4 места и спальники до −5 °C. {DEMO}",
    ),
)

TRIPS: tuple[TripSeed, ...] = (
    TripSeed(
        key="krupyshino-recon",
        squad="vysota",
        title="Разведка у села Крупышино: археология и топография",
        location="с. Крупышино, Орловский район",
        days_from_now=5,
        capacity=15,
        description=f"Полевая школа для новичков: как читать местность и вести полевой журнал. {DEMO}",
        checklist=(
            "Резиновые сапоги (высокие)\n"
            "Плотные рабочие перчатки\n"
            "Термос с чаем и сухой паёк\n"
            "Заряженный телефон с приложением"
        ),
    ),
    TripSeed(
        key="semenkovo-dig",
        squad="vysota",
        title="Вахта Памяти: раскопки у д. Семенково",
        location="д. Семенково",
        days_from_now=19,
        capacity=10,
        description=f"Выезд с ночёвкой. Нужен допуск командира: сначала — полевая школа. {DEMO}",
        checklist="Спальник\nФонарь\nРепеллент\nАптечка\nСменная одежда",
    ),
    TripSeed(
        key="zusha-survey",
        squad="rubezh",
        title="Обследование рубежа по реке Зуше",
        location="г. Мценск",
        days_from_now=12,
        capacity=8,
        description=f"Обход окопов 1941 года с металлоискателем. {DEMO}",
        checklist="Сапоги\nПерчатки\nВода",
    ),
)


def seed(db: Session) -> dict[str, int]:
    """Залить демо-штаб. Возвращает, сколько строк каждого вида теперь в демо-наборе."""
    for item in SQUADS:
        db.merge(
            Squad(
                id=seed_id("squad", item.key),
                name=item.name,
                kind=item.kind,
                region=item.region,
                description=item.description,
                contact="",
                leader_id=SEED_LEADER,
            )
        )
    for item in NEEDS:
        collected = sum(item.donations)
        closed = item.target_amount is not None and collected >= item.target_amount
        db.merge(
            SquadNeed(
                id=seed_id("need", item.key),
                squad_id=seed_id("squad", item.squad),
                kind=item.kind,
                title=item.title,
                description=item.description,
                target_amount=item.target_amount,
                collected_amount=collected,
                status=NeedStatus.closed if closed else NeedStatus.open,
            )
        )
        for index, amount in enumerate(item.donations):
            db.merge(
                Donation(
                    id=seed_id("donation", f"{item.key}:{index}"),
                    need_id=seed_id("need", item.key),
                    donor_id=None,
                    amount=amount,
                    comment="ДЕМО-взнос",
                )
            )
    today = datetime.now(UTC).date()
    for item in TRIPS:
        db.merge(
            VolunteerTrip(
                id=seed_id("trip", item.key),
                squad_id=seed_id("squad", item.squad),
                title=item.title,
                location=item.location,
                starts_on=today + timedelta(days=item.days_from_now),
                capacity=item.capacity,
                description=item.description,
                checklist=item.checklist,
            )
        )
    db.commit()
    return {"squads": len(SQUADS), "needs": len(NEEDS), "trips": len(TRIPS)}


def main() -> None:
    from core.db import SessionLocal, init_db

    init_db()
    with SessionLocal() as db:
        counts = seed(db)
    print(
        "search_hq_service: отрядов — {squads}, потребностей — {needs}, выездов — {trips}".format(
            **counts
        )
    )


if __name__ == "__main__":
    main()
