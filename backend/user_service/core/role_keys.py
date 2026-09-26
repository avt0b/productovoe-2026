"""Ключи NFC-меток, выдающих роль.

Отдельно от сервиса и без зависимостей — этим же модулем пользуется
`scripts/make_role_keys.py`: ключ, который он печатает, и хэш, который
проверяет сервис, обязаны считаться одинаково.
"""

import hashlib
import hmac
import logging

logger = logging.getLogger(__name__)

# Меткой можно стать только тем, кем можно стать по заявке: администратора
# (`is_root`) метка не выдаёт и не отнимает.
GRANTABLE_ROLES = frozenset({"searcher", "local_historian"})


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def parse_keys(raw: str) -> dict[str, str]:
    """`searcher:<sha256>,local_historian:<sha256>` → `{хэш: роль}`.

    Кривую запись пропускаем с предупреждением в лог, а не роняем сервис:
    опечатка в настройке метки не должна гасить профили всем остальным.
    """
    keys: dict[str, str] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        role, _, digest = entry.partition(":")
        role, digest = role.strip(), digest.strip().lower()
        if role not in GRANTABLE_ROLES or len(digest) != 64:
            logger.warning(
                "ROLE_GRANT_KEYS: пропускаю запись для роли %r — ожидалось роль:sha256", role
            )
            continue
        keys[digest] = role
    return keys


def role_for_key(key: str, raw: str) -> tuple[str, str] | None:
    """Роль, которую даёт ключ, и его хэш. Чужой ключ — None."""
    digest = hash_key(key)
    for known, role in parse_keys(raw).items():
        if hmac.compare_digest(known, digest):
            return role, digest
    return None
