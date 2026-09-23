from fastapi import APIRouter

from api.routers import clips, internal, uploads, worker

api_router = APIRouter()
api_router.include_router(clips.router)
api_router.include_router(uploads.router)
api_router.include_router(worker.router)
api_router.include_router(internal.router)
