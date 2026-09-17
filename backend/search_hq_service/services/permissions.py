from core.security import Principal

# Персонал платформы, который может модерировать любой отряд/сбор/выезд.
STAFF_ROLES = {"moderator"}
# Роли, которым разрешено создавать отряды.
SQUAD_CREATOR_ROLES = {"searcher", "moderator"}
# Кто водит экскурсии: краевед, наставник (учитель, сотрудник музея) и модератор.
GUIDE_ROLES = {"local_historian", "mentor", "moderator"}


def is_staff(principal: Principal) -> bool:
    return principal.is_root or principal.role in STAFF_ROLES


def can_create_squad(principal: Principal) -> bool:
    return principal.is_root or principal.role in SQUAD_CREATOR_ROLES


def can_guide(principal: Principal) -> bool:
    return principal.is_root or principal.role in GUIDE_ROLES
