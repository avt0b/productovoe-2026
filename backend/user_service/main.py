from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.deps import CurrentPrincipal
from api.routers import api_router
from core.config import settings
from core.db import init_db
from core.exceptions import AppError


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="user_service — Маршруты победы",
    description="Профили пользователей: семьи, поисковики, краеведы, наставники",
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
    return {"service": "user_service", "status": "ok", "env": settings.app_env}


@app.get("/whoami", tags=["service"])
def whoami(principal: CurrentPrincipal) -> dict:
    return {"user_id": principal.user_id, "role": principal.role, "is_root": principal.is_root}
