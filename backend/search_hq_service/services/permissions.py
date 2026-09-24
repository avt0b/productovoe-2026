from core.security import Principal

# Роли, которым разрешено создавать отряды.
SQUAD_CREATOR_ROLES = {"searcher"}
# Кто водит экскурсии: краевед.
GUIDE_ROLES = {"local_historian"}


def is_staff(principal: Principal) -> bool:
    # Роль moderator убрана — стафф-права остались только у is_root.
    return principal.is_root


def can_create_squad(principal: Principal) -> bool:
    return principal.is_root or principal.role in SQUAD_CREATOR_ROLES


def can_guide(principal: Principal) -> bool:
    return principal.is_root or principal.role in GUIDE_ROLES
