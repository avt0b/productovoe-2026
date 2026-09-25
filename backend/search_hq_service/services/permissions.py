from core.models import SquadKind
from core.security import Principal

# Роли, которым разрешено создавать отряды.
SQUAD_CREATOR_ROLES = {"searcher"}
# Музей и школьный клуб заводит и краевед: он там и работает.
ORGANIZATION_CREATOR_ROLES = {"searcher", "local_historian"}
# Кто водит экскурсии: краевед.
GUIDE_ROLES = {"local_historian"}


def is_staff(principal: Principal) -> bool:
    # Роль moderator убрана — стафф-права остались только у is_root.
    return principal.is_root


def can_create_squad(principal: Principal, kind: SquadKind = SquadKind.squad) -> bool:
    if principal.is_root:
        return True
    roles = SQUAD_CREATOR_ROLES if kind is SquadKind.squad else ORGANIZATION_CREATOR_ROLES
    return principal.role in roles


def can_guide(principal: Principal) -> bool:
    return principal.is_root or principal.role in GUIDE_ROLES
