import logging
from collections.abc import Generator

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings
from core.models.base import Base

logger = logging.getLogger(__name__)

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
    connect_args=_connect_args,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Хакатонный вариант создания схемы. В проде — alembic upgrade head."""
    from core import models  # noqa: F401  (импорт регистрирует модели в metadata)

    Base.metadata.create_all(bind=engine)
    ensure_added_columns(engine)


# Колонки, добавленные в модель после того, как таблица уже появилась в живых
# БД: create_all существующую таблицу не трогает, поэтому досоздаём их сами.
# (таблица, колонка, DDL-тип)
_ADDED_COLUMNS = (
    ("archive_entries", "audio_url", "VARCHAR(500)"),
    ("archive_entries", "point_id", "VARCHAR(36)"),
    ("archive_entries", "poi_id", "VARCHAR(36)"),
)
# Индексы по дописанным колонкам — у свежей базы их создаёт create_all
# (`index=True`), имена совпадают, поэтому IF NOT EXISTS.
_ADDED_INDEXES = (
    ("ix_archive_entries_point_id", "archive_entries", "point_id"),
    ("ix_archive_entries_poi_id", "archive_entries", "poi_id"),
)


def ensure_added_columns(bind: Engine) -> None:
    """Идемпотентно: колонка уже есть — ничего не делает."""
    inspector = inspect(bind)
    with bind.begin() as conn:
        for table, column, ddl_type in _ADDED_COLUMNS:
            existing = {c["name"] for c in inspector.get_columns(table)}
            if column in existing:
                continue
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))
            logger.info("added column %s.%s", table, column)
        for index, table, column in _ADDED_INDEXES:
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS {index} ON {table} ({column})"))
