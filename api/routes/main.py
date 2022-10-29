from fastapi import APIRouter

from api.routes import allocate_route

api_router = APIRouter()

api_router.include_router(allocate_route.router)
