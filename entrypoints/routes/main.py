from fastapi import APIRouter

from entrypoints.routes import allocate_route, batches_route

api_router = APIRouter()

api_router.include_router(allocate_route.router)
api_router.include_router(batches_route.router)
