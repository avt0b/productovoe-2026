from fastapi import APIRouter

from api.routers import achievements, family_heroes, internal, notifications, profiles, uploads

api_router = APIRouter()
api_router.include_router(profiles.router)
api_router.include_router(notifications.router)
api_router.include_router(achievements.router)
api_router.include_router(family_heroes.router)
api_router.include_router(uploads.router)
api_router.include_router(internal.router)
