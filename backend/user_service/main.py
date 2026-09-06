from fastapi import FastAPI

from config import settings

app = FastAPI(
    title="user_service — Маршруты победы",
    description="Профили пользователей: семьи, поисковики, краеведы, наставники",
    version="0.1.0",
)


@app.get("/health", tags=["service"])
def health() -> dict[str, str]:
    return {"service": "user_service", "status": "ok", "env": settings.app_env}
