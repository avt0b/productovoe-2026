from core.security import Principal

# Персонал платформы, который может модерировать любой отряд/сбор/выезд.
STAFF_ROLES = {"moderator"}
# Роли, которым разрешено создавать отряды.
SQUAD_CREATOR_ROLES = {"searcher", "moderator"}


def is_staff(principal: Principal) -> bool:
    return principal.is_root or principal.role in STAFF_ROLES


def can_create_squad(principal: Principal) -> bool:
    return principal.is_root or principal.role in SQUAD_CREATOR_ROLES
