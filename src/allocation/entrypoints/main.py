from fastapi import FastAPI
from src.allocation.entrypoints.routes.main import api_router
from src.allocation.adapters import orm

# это конечно не по-христиански, но надеюсь, что уйдем от этого в след главах
orm.start_mappers()
fastapi_app = FastAPI()

fastapi_app.include_router(api_router)
