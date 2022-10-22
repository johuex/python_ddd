from sqlalchemy.orm import Session

import repository
from models import domain_models


def insert_order_line(session: Session) -> str:
    # для создания данных перед тестом можно использовать сырой SQL
    session.execute(
        'INSERT INTO order_lines (orderid, sku, qty)'
        ' VALUES ("order1", "GENERIC-SOFA", 12)'
    )
    [[orderline_id]] = session.execute(
        'SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku',
        dict(orderid="order1", sku="GENERIC-SOFA")
    )
    return orderline_id


def insert_batch(session: Session, batch_id: str) -> str:
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        ' VALUES (:batch_id, "GENERIC-SOFA", 100, null)',
        dict(batch_id=batch_id),
    )
    [[batch_id]] = session.execute(
        'SELECT id FROM batches WHERE reference=:batch_id AND sku="GENERIC-SOFA"',
        dict(batch_id=batch_id),
    )
    return batch_id


def insert_allocation(session: Session, orderline_id: str, batch_id: str) -> str:
    session.execute(
        "INSERT INTO allocations (orderline_id, batch_id)"
        " VALUES (:orderline_id, :batch_id)",
        dict(orderline_id=orderline_id, batch_id=batch_id),
    )


def get_allocations(session, batchid) -> set[domain_models.OrderLine]:
    rows = list(
        session.execute(
            "SELECT orderid"
            " FROM allocations"
            " JOIN order_lines ON allocations.orderline_id = order_lines.id"
            " JOIN batches ON allocations.batch_id = batches.id"
            " WHERE batches.reference = :batchid",
            dict(batchid=batchid),
        )
    )
    return {row[0] for row in rows}


class TestRepository:

    def test_repository_can_save_a_batch(self, db_session):
        """

        """
        batch = domain_models.Batch("batch1", "RUSTY-SOAPDISH", 100, eta=None)
        repo = repository.SqlAlchemyRepository(db_session)

        repo.add(batch)  # тестируемый метод

        db_session.commit()  # операцию фиксации специально держим вне репозитория
        # для проверки можно использовать сырой SQL
        rows = list(db_session.execute('SELECT reference, sku, _purchased_quantity, eta FROM "batches"'))
        assert rows == [("batch1", "RUSTY-SOAPDISH", 100, None)]

    def test_repository_can_retrieve_a_batch_with_allocations(self, db_session):
        """

        """
        orderline_id = insert_order_line(db_session)
        batch1_id = insert_batch(db_session, "batch1")
        insert_batch(db_session, "batch2")
        insert_allocation(db_session, orderline_id, batch1_id)
        repo = repository.SqlAlchemyRepository(db_session)

        retrieved = repo.get("batch1")  # тестируемый метод

        expected = domain_models.Batch("batch1", "GENERIC-SOFA", 100, eta=None)
        assert retrieved == expected  # Batch.__eq__ сравнивает только ссылку
        assert retrieved.sku == expected.sku
        assert retrieved._purchased_quantity == expected._purchased_quantity
        assert retrieved._allocations == {domain_models.OrderLine("order1", "GENERIC-SOFA", 12), }

    def test_updating_a_batch(self, db_session):
        order1 = domain_models.OrderLine("order1", "WEATHERED-BENCH", 10)
        order2 = domain_models.OrderLine("order2", "WEATHERED-BENCH", 20)
        batch = domain_models.Batch("batch1", "WEATHERED-BENCH", 100, eta=None)
        batch.allocate(order1)

        repo = repository.SqlAlchemyRepository(db_session)
        repo.add(batch)
        db_session.commit()

        batch.allocate(order2)
        repo.add(batch)
        db_session.commit()

        assert get_allocations(db_session, "batch1") == {"order1", "order2"}