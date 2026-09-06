from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import api_router
from core.config import settings
from core.db import init_db
from core.exceptions import AppError
from services.bootstrap import ensure_bootstrap_admin
from services.upstream import Upstream


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_bootstrap_admin()
    # Один HTTP-клиент на всё приложение: веерный опрос сервисов идёт через него.
    app.state.upstream = Upstream()
    try:
        yield
    finally:
        await app.state.upstream.aclose()


app = FastAPI(
    title="admin_service — Маршруты победы",
    description=(
        "Панель администратора: собственная аутентификация с TOTP, "
        "сводный дашборд по всем сервисам, операции над данными и журнал аудита"
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Админка — отдельное веб-приложение, ходит с другого origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(api_router)


@app.get("/health", tags=["service"])
def health() -> dict[str, str]:
    return {"service": "admin_service", "status": "ok", "env": settings.app_env}
