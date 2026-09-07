from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.routers import api_router
from core.config import settings
from core.db import init_db
from core.exceptions import AppError
from services.bootstrap import ensure_root_user


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    ensure_root_user()
    yield
 

app = FastAPI(
    title="auth_service — Маршруты победы",
    description="Регистрация, вход (email + пароль), выдача и ротация JWT",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(AppError)
async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(api_router)


@app.get("/health", tags=["service"])
def health() -> dict[str, str]:
    return {"service": "auth_service", "status": "ok", "env": settings.app_env}
