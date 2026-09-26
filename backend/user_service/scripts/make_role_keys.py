"""Ключи для двух NFC-меток, выдающих роль: поисковика и краеведа.

    cd backend/user_service && uv run python -m scripts.make_role_keys

Печатает две ссылки — их записывают на метки (экран «NFC-метка» в
приложении, поле «Экран») — и строку ROLE_GRANT_KEYS для `.env` сервиса. В
настройке только хэши: ключи живут на метках и больше нигде, в git и в чаты
их не кладите. Метка скопирована или потерялась — выпустите новые ключи и
замените строку, старые метки сразу перестанут работать.
"""

import secrets

from core.role_keys import hash_key

LABELS = {"searcher": "поисковик", "local_historian": "краевед"}


def main() -> None:
    entries = []
    for role, label in LABELS.items():
        # 32 случайных байта — 256 бит, в base64url 43 символа.
        key = secrets.token_urlsafe(32)
        entries.append(f"{role}:{hash_key(key)}")
        print(f"Метка «{label}»: marshruty://grant?k={key}")
    print()
    print("В .env user_service (или в корневой .env для docker compose):")
    print(f"ROLE_GRANT_KEYS={','.join(entries)}")


if __name__ == "__main__":
    main()
