"""Погибшие на Орловщине из ОБД «Мемориал» — в Книгу памяти (народный архив).

Запуск из `backend/archive_service` (в контейнере — из `/app`):
    uv run python -m scripts.import_obd_fighters fighters.json
Файл — выгрузка поимённых списков захоронений: JSON-массив (можно .json.gz) с
полями id, full_name, birth_year, death_date, rank, unit, burial_place, lat, lon,
source, biography.

Каждый боец — подтверждённая карточка (`soldier_card`, `verified`): это
официальная база, а не предложение пользователя. Ссылка на анкету уходит в
текст строкой «Источник: <url>» — веб-архив показывает её кнопкой.

Идемпотентный: id записи — id бойца из выгрузки (uuid5), повторный запуск
обновляет те же строки, а не плодит дубли. Схему создаёт сам.
"""

import gzip
import json
import re
import sys
from collections.abc import Iterable, Iterator
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from core.models import ArchiveEntry, EntryKind, EntryStatus

# Кто «предложил» и «подтвердил» записи импорта — не человек, а источник.
IMPORT_AUTHOR = "import-obd-memorial"
REVIEW_NOTE = "Импорт: ОБД «Мемориал», поимённые списки захоронений Орловской области"
BATCH = 2000

_URL = re.compile(r"https?://\S+")
# Обновляются при повторном импорте; автор, статус и дата создания — нет.
_UPDATABLE = ("title", "body", "lat", "lon", "event_date", "date_text", "updated_at")


def load(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig") as f:
        return json.load(f)


def to_row(fighter: dict, now: datetime) -> dict | None:
    title = " ".join(str(fighter.get("full_name") or "").split())[:255]
    if not fighter.get("id") or not title:
        return None
    death = _parse_date(fighter.get("death_date"))
    birth_year = fighter.get("birth_year")
    lat, lon = fighter.get("lat"), fighter.get("lon")
    if not (_in_range(lat, 90) and _in_range(lon, 180)):
        lat = lon = None
    return {
        "id": str(fighter["id"]),
        "kind": EntryKind.soldier_card,
        "title": title,
        "body": _body(fighter),
        "lat": lat,
        "lon": lon,
        "event_date": death,
        "date_text": _date_text(birth_year, death, fighter.get("death_date")),
        "submitted_by": IMPORT_AUTHOR,
        "status": EntryStatus.verified,
        "verified_by": IMPORT_AUTHOR,
        "reviewed_at": now,
        "review_note": REVIEW_NOTE,
        "created_at": now,
        "updated_at": now,
    }


def import_fighters(db: Session, fighters: Iterable[dict]) -> int:
    now = datetime.now(UTC)
    written = 0
    for batch in _batches(filter(None, (to_row(f, now) for f in fighters)), BATCH):
        db.execute(_upsert(db, batch))
        db.commit()
        written += len(batch)
        print(f"  … {written}", flush=True)
    return written


def _upsert(db: Session, rows: list[dict]):
    table = ArchiveEntry.__table__
    if db.get_bind().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    stmt = insert(table).values(rows)
    return stmt.on_conflict_do_update(
        index_elements=[table.c.id],
        set_={column: stmt.excluded[column] for column in _UPDATABLE},
    )


def _body(fighter: dict) -> str:
    parts = [str(fighter.get("biography") or "").strip()]
    source = str(fighter.get("source") or "").strip()
    url = _URL.search(source)
    if source:
        parts.append(f"Данные: {_URL.sub('', source).strip(' ,;')}.")
    if url:
        parts.append(f"Источник: {url.group(0)}")
    return "\n\n".join(part for part in parts if part)


def _date_text(birth_year: object, death: date | None, raw_death: object) -> str:
    born = str(birth_year) if birth_year else "?"
    if death:
        died = death.strftime("%d.%m.%Y")
    elif raw_death:
        died = str(raw_death)[:40]
    else:
        died = "?"
    return "" if born == died == "?" else f"{born} — {died}"


def _parse_date(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value)) if value else None
    except ValueError:
        return None


def _in_range(value: object, limit: float) -> bool:
    return isinstance(value, int | float) and -limit <= value <= limit


def _batches(rows: Iterable[dict], size: int) -> Iterator[list[dict]]:
    batch: list[dict] = []
    for row in rows:
        batch.append(row)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Использование: python -m scripts.import_obd_fighters <fighters.json[.gz]>"
        )
    from core.db import SessionLocal, init_db

    fighters = load(Path(sys.argv[1]))
    print(f"archive_service: в файле {len(fighters)} бойцов, импортирую…", flush=True)
    init_db()
    with SessionLocal() as db:
        written = import_fighters(db, fighters)
    print(f"archive_service: в Книге памяти {written} карточек из ОБД «Мемориал»")


if __name__ == "__main__":
    main()
