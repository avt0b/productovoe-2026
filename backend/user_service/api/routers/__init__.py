from fastapi import APIRouter

from api.routers import profiles

api_router = APIRouter()
api_router.include_router(profiles.router)
