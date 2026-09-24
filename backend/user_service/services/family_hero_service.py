from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.exceptions import NotFound, PermissionDenied
from core.models import FamilyHero
from core.security import Principal
from repositories.family_hero_repository import FamilyHeroRepository


class FamilyHeroService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = FamilyHeroRepository(db)

    def for_owner(self, owner_id: str) -> Sequence[FamilyHero]:
        return self.repo.for_owner(owner_id)

    def create(self, principal: Principal, data: dict) -> FamilyHero:
        hero = self.repo.add(FamilyHero(owner_id=principal.user_id, **data))
        self.db.commit()
        self.db.refresh(hero)
        return hero

    def update(self, principal: Principal, hero_id: str, data: dict) -> FamilyHero:
        hero = self._owned(principal, hero_id)
        for field, value in data.items():
            setattr(hero, field, value)
        self.db.commit()
        self.db.refresh(hero)
        return hero

    def delete(self, principal: Principal, hero_id: str) -> None:
        hero = self._owned(principal, hero_id)
        self.repo.delete(hero)
        self.db.commit()

    def _owned(self, principal: Principal, hero_id: str) -> FamilyHero:
        hero = self.repo.get(hero_id)
        if hero is None:
            raise NotFound("Запись не найдена")
        if hero.owner_id != principal.user_id and not principal.is_root:
            raise PermissionDenied("Изменять запись может только владелец")
        return hero
