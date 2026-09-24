from fastapi import APIRouter

from api.routers import (
    achievements,
    family_heroes,
    family_links,
    internal,
    notifications,
    profiles,
    role_applications,
    uploads,
)

api_router = APIRouter()
api_router.include_router(profiles.router)
api_router.include_router(notifications.router)
api_router.include_router(achievements.router)
api_router.include_router(family_heroes.router)
api_router.include_router(family_links.router)
api_router.include_router(role_applications.router)
api_router.include_router(uploads.router)
api_router.include_router(internal.router)
