from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import api_router
from core.config import settings
from core.db import init_db
from core.exceptions import AppError


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="archive_service — Маршруты победы",
    description="«Народный архив» / «Живая память»: пользовательские записи с верификацией",
    version="0.1.0",
    lifespan=lifespan,
)

# Клиентское приложение (браузер и APK) ходит в сервис напрямую, с другого origin.
# Токен идёт в заголовке, cookie нет — credentials не нужны.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(api_router)


@app.get("/health", tags=["service"])
def health() -> dict[str, str]:
    return {"service": "archive_service", "status": "ok", "env": settings.app_env}
