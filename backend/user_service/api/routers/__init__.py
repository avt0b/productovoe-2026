from fastapi import APIRouter

from api.routers import internal, profiles

api_router = APIRouter()
api_router.include_router(profiles.router)
api_router.include_router(internal.router)
