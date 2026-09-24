from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import FamilyHero


class FamilyHeroRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, hero_id: str) -> FamilyHero | None:
        return self.db.get(FamilyHero, hero_id)

    def add(self, hero: FamilyHero) -> FamilyHero:
        self.db.add(hero)
        self.db.flush()
        return hero

    def delete(self, hero: FamilyHero) -> None:
        self.db.delete(hero)

    def for_owner(self, owner_id: str) -> Sequence[FamilyHero]:
        return self.db.scalars(
            select(FamilyHero)
            .where(FamilyHero.owner_id == owner_id)
            .order_by(FamilyHero.created_at.asc())
        ).all()
