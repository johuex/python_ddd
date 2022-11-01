from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services import config
from api.routes.main import api_router
from models import orm_models

# это конечно не по-христиански, но надеюсь, что уйдем от этого в след главах
orm_models.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
fastapi_app = FastAPI()

fastapi_app.include_router(api_router)
