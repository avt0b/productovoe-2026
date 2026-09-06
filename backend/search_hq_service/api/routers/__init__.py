from fastapi import APIRouter

from api.routers import internal, needs, squads, trips

api_router = APIRouter()
api_router.include_router(squads.router)
api_router.include_router(needs.router)
api_router.include_router(trips.router)
api_router.include_router(internal.router)
