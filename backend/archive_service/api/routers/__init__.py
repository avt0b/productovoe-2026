from fastapi import APIRouter

from api.routers import entries

api_router = APIRouter()
api_router.include_router(entries.router)
