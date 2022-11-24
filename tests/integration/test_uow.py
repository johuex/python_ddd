import pytest

from src.allocation.models import domain_models
from src.allocation.service_layer import unit_of_work


def insert_batch(session, ref, sku, qty, eta):
    session.execute(
        'INSERT INTO batches (reference, sku, _purchased_quantity, eta)'
        ' VALUES (:ref, :sku, :qty, :eta)',
        dict(ref=ref, sku=sku, qty=qty, eta=eta)
    )


def get_allocated_batch_ref(session, orderid, sku):
    [[orderlineid]] = session.execute(
        'SELECT id FROM order_lines WHERE orderid=:orderid AND'
        'sku=:sku',
        dict(orderid=orderid, sku=sku)
    )
    [[batchref]] = session.execute(
        'SELECT b.reference FROM allocations JOIN batches AS b ON'
        ' batch_id = b.id'
        ' WHERE orderline_id=:orderlineid',
        dict(orderlineid=orderlineid)
    )
    return batchref


class TestUoW:
    def test_uow_can_retrieve_a_batch_and_allocate_to_it(self, session_factory):
        """
        1. В БД кладем партию
        2. Размещаем в партии товарную позицию
        3. Commit изменения
        ОР: позиция разместилась в партии
        """
        session = session_factory()
        insert_batch(session, 'batch1', 'HIPSTER-WORKBENCH', 100, None)
        session.commit()
        uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
        with uow:
            batch = uow.batches.get(reference='batch1')  # access to repo through uow
            line = domain_models.OrderLine('o1', 'HIPSTER-WORKBENCH', 10)
            batch.allocate(line)
            uow.commit()
        batchref = get_allocated_batch_ref(session, 'o1', 'HIPSTER-WORKBENCH')
        assert batchref == 'batch1'

    def test_rolls_back_uncommitted_work_by_default(self, session_factory):
        """
        1. В БД кладем партию без commit'a изменений
        2. Получаем список всех партий
        ОР: партий нет: []
        """
        uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
        with uow:
            insert_batch(uow.session, 'batch1', 'MEDIUM-PLINTH', 100, None)

        new_session = session_factory()
        rows = list(new_session.execute('SELECT * FROM "batches"'))
        assert rows == []

    def test_rolls_back_on_error(self, session_factory):
        """
        1. В БД кладем партию
        2. В пределах UoW вызываем любое исключение
        3. Получаем список всех партий
        ОР: партий нет: []
        """
        class SomeException(Exception):
            pass

        uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
        with pytest.raises(SomeException):
            with uow:
                insert_batch(uow.session, 'batch1', 'LARGE-FORK', 100, None)
                raise SomeException()

        new_session = session_factory()
        rows = list(new_session.execute('SELECT * FROM "batches"'))
        assert rows == []
