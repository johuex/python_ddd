import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

import config
from helpers.utils import wait_for_postgres_to_come_up
from adapters.orm import metadata, start_mappers


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


@pytest.fixture
def add_stock(postgres_session):
    """
    Фикстура, добавляющая данные в тестах API и удаляющая их после теста
    """
    batches_added = set()
    skus_added = set()

    def _add_stock(lines):
        # в тестах можем использовать сырой SQL
        for ref, sku, qty, eta in lines:
            postgres_session.execute(
                "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
                " VALUES (:ref, :sku, :qty, :eta)",
                dict(ref=ref, sku=sku, qty=qty, eta=eta),
            )
            [[batch_id]] = postgres_session.execute(
                "SELECT id FROM batches WHERE reference=:ref AND sku=:sku",
                dict(ref=ref, sku=sku),
            )
            batches_added.add(batch_id)
            skus_added.add(sku)
        postgres_session.commit()

    yield _add_stock

    # в тестах можем использовать сырой SQL
    for batch_id in batches_added:
        postgres_session.execute(
            "DELETE FROM allocations WHERE batch_id=:batch_id",
            dict(batch_id=batch_id),
        )
        postgres_session.execute(
            "DELETE FROM batches WHERE id=:batch_id", dict(batch_id=batch_id),
        )
    for sku in skus_added:
        postgres_session.execute(
            "DELETE FROM order_lines WHERE sku=:sku", dict(sku=sku),
        )
        postgres_session.commit()
