from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.medicines import router as medicines_router
from app.api.v1.plans import router as plans_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(medicines_router)
api_router.include_router(plans_router)
