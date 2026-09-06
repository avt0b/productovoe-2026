from fastapi import APIRouter

from api.routers import admin, auth

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
