from fastapi import FastAPI

from config import settings

app = FastAPI(
    title="auth_service — Маршруты победы",
    description="Регистрация, вход, выдача и ротация JWT",
    version="0.1.0",
)


@app.get("/health", tags=["service"])
def health() -> dict[str, str]:
    return {"service": "auth_service", "status": "ok", "env": settings.app_env}
