import re

from core.config import settings

# Базовые матерные корни. Список короткий и ловит только прямой текст —
# не претендует на полноту и не пытается угадывать обход вида "п_и_з_д".
_BASE_ROOTS = [
    "хуй",
    "хуе",
    "хуё",
    "пизд",
    "еба",
    "ёба",
    "ебу",
    "бляд",
    "мудак",
    "мудил",
]


def _extra_words() -> list[str]:
    """Слова сверх мата — решает оператор платформы через ENV, не код."""
    return [w.strip() for w in settings.chat_banned_words.split(",") if w.strip()]


def _pattern() -> re.Pattern[str]:
    parts = [re.escape(root) for root in _BASE_ROOTS + _extra_words()]
    return re.compile("|".join(parts), re.IGNORECASE)


def contains_banned_content(text: str) -> bool:
    return bool(_pattern().search(text))
