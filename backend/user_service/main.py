from fastapi import FastAPI

from api.deps import CurrentPrincipal
from core.config import settings

app = FastAPI(
    title="user_service — Маршруты победы",
    description="Профили пользователей: семьи, поисковики, краеведы, наставники",
    version="0.1.0",
)


@app.get("/health", tags=["service"])
def health() -> dict[str, str]:
    return {"service": "user_service", "status": "ok", "env": settings.app_env}


@app.get("/whoami", tags=["profile"])
def whoami(principal: CurrentPrincipal) -> dict:
    """Пример защищённого эндпоинта: читает identity из JWT auth_service."""
    return {
        "user_id": principal.user_id,
        "role": principal.role,
        "is_root": principal.is_root,
    }
