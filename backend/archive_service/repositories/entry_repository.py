from collections.abc import Sequence

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from core.models import ArchiveEntry, EntryKind, EntryStatus


class EntryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, entry_id: str) -> ArchiveEntry | None:
        return self.db.get(ArchiveEntry, entry_id)

    def add(self, entry: ArchiveEntry) -> ArchiveEntry:
        self.db.add(entry)
        self.db.flush()
        return entry

    def delete(self, entry: ArchiveEntry) -> None:
        self.db.delete(entry)

    def count_verified_by(self, user_id: str) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(ArchiveEntry)
                .where(
                    ArchiveEntry.verified_by == user_id, ArchiveEntry.status == EntryStatus.verified
                )
            )
            or 0
        )

    def search(
        self,
        *,
        status: EntryStatus | None = None,
        kind: EntryKind | None = None,
        submitted_by: str | None = None,
        point_id: str | None = None,
        poi_id: str | None = None,
        q: str | None = None,
        prefix: str | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        sort: str = "new",
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ArchiveEntry]:
        stmt = select(ArchiveEntry)
        if status is not None:
            stmt = stmt.where(ArchiveEntry.status == status)
        if kind is not None:
            stmt = stmt.where(ArchiveEntry.kind == kind)
        if submitted_by is not None:
            stmt = stmt.where(ArchiveEntry.submitted_by == submitted_by)
        if point_id is not None:
            stmt = stmt.where(ArchiveEntry.point_id == point_id)
        if poi_id is not None:
            stmt = stmt.where(ArchiveEntry.poi_id == poi_id)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(ArchiveEntry.title.ilike(like) | ArchiveEntry.body.ilike(like))
        if prefix:
            stmt = stmt.where(ArchiveEntry.title.ilike(f"{_escape_like(prefix)}%", escape="\\"))
        if bbox is not None:
            min_lat, min_lon, max_lat, max_lon = bbox
            stmt = stmt.where(
                ArchiveEntry.lat.is_not(None),
                ArchiveEntry.lon.is_not(None),
                ArchiveEntry.lat.between(min_lat, max_lat),
                ArchiveEntry.lon.between(min_lon, max_lon),
            )
        # «title» — как в Книге памяти, по алфавиту; id добивает порядок при
        # одинаковых фамилиях, иначе страницы съезжали бы между запросами.
        if sort == "title":
            # «[неизвестно] Алексей» из ОБД — в конец: скобка иначе встаёт раньше «А».
            unnamed = case((func.substr(ArchiveEntry.title, 1, 1) == "[", 1), else_=0)
            order = [unnamed, ArchiveEntry.title.asc(), ArchiveEntry.id.asc()]
            if q:
                # Ищут обычно фамилию: совпадения в заголовке — раньше тех, где
                # слово нашлось только в тексте (деревня Жуково у «Жуков»).
                order.insert(0, case((ArchiveEntry.title.ilike(f"%{q}%"), 0), else_=1))
        else:
            order = [ArchiveEntry.created_at.desc(), ArchiveEntry.id.asc()]
        return self.db.scalars(stmt.order_by(*order).limit(limit).offset(offset)).all()

    def summary(self, *, status: EntryStatus, kind: EntryKind | None = None) -> dict:
        """Сводка по разделу архива для шапки: сколько имён, у скольких известна
        дата и точка на карте, с каких букв начинаются заголовки."""
        where = [ArchiveEntry.status == status]
        if kind is not None:
            where.append(ArchiveEntry.kind == kind)
        has_date = (ArchiveEntry.event_date.is_not(None)) | (ArchiveEntry.date_text != "")
        on_map = ArchiveEntry.lat.is_not(None) & ArchiveEntry.lon.is_not(None)
        total, with_date, mapped = self.db.execute(
            select(
                func.count(),
                func.count().filter(has_date),
                func.count().filter(on_map),
            )
            .select_from(ArchiveEntry)
            .where(*where)
        ).one()
        letters = self.db.scalars(
            select(func.upper(func.substr(ArchiveEntry.title, 1, 1))).where(*where).distinct()
        ).all()
        return {
            "total": total,
            "with_date": with_date,
            "on_map": mapped,
            # Только буквы: «[неизвестно] Алексей» из ОБД в алфавит не выносим —
            # такие записи есть в общем списке и в поиске.
            "letters": sorted(
                {letter for letter in letters if letter and letter.isalpha()}, key=_letter_key
            ),
        }


# Русский алфавит в своём порядке (Ё — после Е), остальные буквы — следом.
_ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"


def _letter_key(letter: str) -> tuple[int, str]:
    index = _ALPHABET.find(letter)
    return (index if index >= 0 else len(_ALPHABET), letter)


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
