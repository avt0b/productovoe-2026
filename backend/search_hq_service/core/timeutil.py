from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    """Дата с часовым поясом UTC.

    SQLite (тесты) отдаёт `DateTime(timezone=True)` без пояса, Postgres — с ним.
    Без приведения сравнение «сейчас» со сроком сбора падает на смеси naive/aware.
    """
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
