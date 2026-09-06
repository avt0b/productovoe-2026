from fastapi import APIRouter

from api.routers import accounts, audit, auth, dashboard, operations

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(operations.router)
api_router.include_router(accounts.router)
api_router.include_router(audit.router)
