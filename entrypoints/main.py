from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from entrypoints.routes.main import api_router
from adapters import orm

# это конечно не по-христиански, но надеюсь, что уйдем от этого в след главах
orm_models.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
fastapi_app = FastAPI()

fastapi_app.include_router(api_router)
