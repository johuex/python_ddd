import uvicorn
from fastapi import FastAPI
from sqlalchemy import create_engine

from src.allocation.adapters.orm import metadata
from src.allocation.core import config
from src.allocation.entrypoints.routes.main import api_router
from src.allocation.adapters import orm
from src.allocation.helpers.utils import wait_for_postgres_to_come_up

orm.start_mappers()  # это конечно не по-христиански, но надеюсь, что уйдем от этого в след главах
fastapi_app = FastAPI()

fastapi_app.include_router(api_router)

if __name__ == "__main__":
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    metadata.create_all(engine)  # создать таблицы в БД автоматически
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
