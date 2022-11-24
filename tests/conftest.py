import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

from src.allocation import config
from src.allocation.helpers.utils import wait_for_postgres_to_come_up
from src.allocation.adapters.orm import metadata, start_mappers


@pytest.fixture
def in_memory_db():
    """
    Возвращает engine к БД SQLite в RAM
    """
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)  # создать таблицы в БД автоматически
    return engine


@pytest.fixture
def sqlite_session(in_memory_db):
    """
    Перед созданием соединения к БД SQLite мэтчим domain_models и orm_models между собой, возвращает соединение
    """
    start_mappers()
    yield sessionmaker(bind=in_memory_db)()
    clear_mappers()


@pytest.fixture(scope="session")
def postgres_db():
    """
    Возвращает engine к БД Postgres
    """
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    metadata.create_all(engine)  # создать таблицы в БД автоматически
    return engine


@pytest.fixture
def postgres_session(postgres_db):
    """
    Перед созданием соединения к БД Postgres мэтчим domain_models и orm_models между собой, возвращает соединение
    """
    start_mappers()
    yield sessionmaker(bind=postgres_db)()
    clear_mappers()
