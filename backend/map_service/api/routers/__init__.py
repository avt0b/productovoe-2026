from fastapi import APIRouter

from api.routers import internal, last_stand, poi

api_router = APIRouter()
api_router.include_router(poi.router)
api_router.include_router(last_stand.router)
api_router.include_router(internal.router)
