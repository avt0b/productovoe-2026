from fastapi import APIRouter

from api.routers import clips, internal, worker

api_router = APIRouter()
api_router.include_router(clips.router)
api_router.include_router(worker.router)
api_router.include_router(internal.router)
