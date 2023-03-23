import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

from src.allocation import bootstrap
from src.allocation.core import config
from src.allocation.helpers.utils import wait_for_postgres_to_come_up
from src.allocation.adapters.orm import metadata, start_mappers
from tests import fake_services


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
    Перед созданием соединения к БД SQLite мэтчим domain_models и orm_models между собой, возвращает sessionmaker
    """
    start_mappers()
    yield sessionmaker(bind=in_memory_db)
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
    Перед созданием соединения к БД Postgres мэтчим domain_models и orm_models между собой, возвращает sessionmaker
    """
    start_mappers()  # из-за bus = bootstrap() в bootstrap
    yield sessionmaker(bind=postgres_db)
    clear_mappers()


@pytest.fixture(scope="function")
def fake_bus():
    mbus = bootstrap.bootstrap(
        start_orm=False,
        uow=fake_services.FakeUnitOfWork(),
        message_bus=fake_services.FakeMessageBus
    )
    yield mbus


@pytest.fixture(scope="function")
def real_bus(postgres_session):
    mbus = bootstrap.bootstrap(
        start_orm=False,
    )
    yield mbus
