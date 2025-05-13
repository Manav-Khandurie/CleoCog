from fastapi import APIRouter
from app.api.v1.endpoints import embed,health

api_router = APIRouter()
api_router.include_router(embed.router)
api_router.include_router(health.router)
