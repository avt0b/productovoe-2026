from fastapi import APIRouter

from api.routers import routes, waypoints

api_router = APIRouter()
api_router.include_router(routes.router)
api_router.include_router(waypoints.router)
