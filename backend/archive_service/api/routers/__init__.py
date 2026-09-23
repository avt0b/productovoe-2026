from fastapi import APIRouter

from api.routers import entries, internal, uploads

api_router = APIRouter()
api_router.include_router(entries.router)
api_router.include_router(uploads.router)
api_router.include_router(internal.router)
