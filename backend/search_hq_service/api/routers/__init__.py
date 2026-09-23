from fastapi import APIRouter

from api.routers import excursions, guides, internal, needs, payments, squads, trips

api_router = APIRouter()
api_router.include_router(squads.router)
api_router.include_router(needs.router)
api_router.include_router(trips.router)
api_router.include_router(excursions.router)
api_router.include_router(guides.router)
api_router.include_router(payments.router)
api_router.include_router(internal.router)
