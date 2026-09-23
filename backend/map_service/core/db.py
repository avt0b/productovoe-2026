import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
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


_postgis_ready = False


def postgis_available() -> bool:
    """True только если _ensure_postgis() реально отработала на этом Postgres.

    Сервисы сверяются с этим флагом (а не просто с диалектом БД) перед тем,
    как идти в `*_repository.nearby_postgis` — иначе на Postgres без PostGIS
    (расширение не установлено, старой версии, нет прав) каждый nearby-запрос
    падал бы на несуществующей колонке `geog`.
    """
    return _postgis_ready


def init_db() -> None:
    """Хакатонный вариант создания схемы. В проде — alembic upgrade head."""
    global _postgis_ready
    from core import models  # noqa: F401  (импорт регистрирует модели в metadata)

    Base.metadata.create_all(bind=engine)

    if engine.dialect.name == "postgresql":
        _postgis_ready = _ensure_postgis()


# Таблицы с lat/lon, для которых нужен индексированный geo-поиск.
_GEO_TABLES = ("points_of_interest", "last_stand_points")


def _ensure_postgis() -> bool:
    """Прод-апгрейд, описанный в core/geo.py: реальный geo-поиск через PostGIS
    (ST_DWithin + GiST-индекс) вместо bbox-фильтра и haversine в Python.

    `geog` — сгенерированная колонка (STORED), она сама пересчитывается из
    lat/lon на каждой записи, отдельно её писать не нужно. На sqlite (тесты)
    этот блок не выполняется — там остаётся Python-фолбэк в core/geo.py и
    репозиториях (`search` + `nearby` в сервисах).

    Отказ (нет расширения на сервере, не хватило прав и т.п.) не должен ронять
    старт сервиса — тогда сервисы просто остаются на Python-фолбэке.
    """
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            for table in _GEO_TABLES:
                conn.execute(
                    text(
                        f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS geog "
                        "geography(Point, 4326) "
                        "GENERATED ALWAYS AS "
                        "(ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography) STORED"
                    )
                )
                conn.execute(
                    text(f"CREATE INDEX IF NOT EXISTS ix_{table}_geog ON {table} USING GIST (geog)")
                )
    except DBAPIError as exc:
        logger.warning("PostGIS недоступен, остаёмся на Python-фолбэке geo-поиска: %s", exc)
        return False
    return True
