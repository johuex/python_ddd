import threading
import time
import traceback

import pytest

from src.allocation.helpers.utils import random_sku, random_batchref, random_orderid
from src.allocation.models import domain
from src.allocation.services import unit_of_work


def insert_batch(session, ref, sku, qty, eta, version=1):
    session.execute(
        "INSERT INTO products (sku, version) VALUES (:sku, :version)",
        dict(sku=sku, version=version,)
    )
    session.execute(
        'INSERT INTO batches (reference, sku, _purchased_quantity, eta)'
        ' VALUES (:ref, :sku, :qty, :eta)',
        dict(ref=ref, sku=sku, qty=qty, eta=eta)
    )


def get_allocated_batch_ref(session, orderid, sku):
    [[orderlineid]] = session.execute(
        'SELECT id FROM order_lines WHERE orderid=:orderid AND'
        ' sku=:sku',
        dict(orderid=orderid, sku=sku)
    )
    [[batchref]] = session.execute(
        'SELECT b.reference FROM allocations JOIN batches AS b ON'
        ' batch_id = b.id'
        ' WHERE orderline_id=:orderlineid',
        dict(orderlineid=orderlineid)
    )
    return batchref


def try_to_allocate(orderid, sku, exceptions):
    line = domain.OrderLine(orderid, sku, 10)
    try:
        with unit_of_work.SqlAlchemyUnitOfWork() as uow:
            product = uow.products.get(sku=sku)
            product.allocate(line)
            time.sleep(1)
            uow.commit()
    except Exception as e:
        print(traceback.format_exc())
        exceptions.append(e)


def delete_all_from_db(session):
    session.execute("delete from allocations;")
    session.execute("delete from batches;")
    session.execute("delete from order_lines;")
    session.execute("delete from products;")


class TestUoW:
    @pytest.fixture(scope="function", autouse=True)
    def clear_db_fixture(self, postgres_session):
        session = postgres_session()
        delete_all_from_db(session)
        session.commit()
        session.close()


    def test_uow_can_retrieve_a_batch_and_allocate_to_it_returns_ok(self, postgres_session):
        """
        1. В БД кладем партию
        2. Размещаем в партии товарную позицию
        3. Commit изменения
        ОР: позиция разместилась в партии
        """
        session = postgres_session()
        insert_batch(session, 'batch1', 'HIPSTER-WORKBENCH', 100, None)
        session.commit()

        uow = unit_of_work.SqlAlchemyUnitOfWork()
        with uow:
            product = uow.products.get(sku='HIPSTER-WORKBENCH')  # access to repo through uow
            line = domain.OrderLine('o1', 'HIPSTER-WORKBENCH', 10)
            product.allocate(line)
            uow.commit()
        batchref = get_allocated_batch_ref(session, 'o1', 'HIPSTER-WORKBENCH')
        session.close()
        assert batchref == 'batch1'

    def test_rolls_back_uncommitted_work_by_default_returns_ok(self, postgres_session):
        """
        1. В БД кладем партию без commit'a изменений
        2. Получаем список всех партий
        ОР: партий нет: []
        """
        uow = unit_of_work.SqlAlchemyUnitOfWork()
        with uow:
            insert_batch(uow.session, 'batch1', 'MEDIUM-PLINTH', 100, None)

        new_session = postgres_session()
        rows = list(new_session.execute('SELECT * FROM "batches"'))
        assert rows == []

    def test_rolls_back_on_error_returns_ok(self, postgres_session):
        """
        1. В БД кладем партию
        2. В пределах UoW вызываем любое исключение
        3. Получаем список всех партий
        ОР: партий нет: []
        """
        class SomeException(Exception):
            pass

        uow = unit_of_work.SqlAlchemyUnitOfWork()
        with pytest.raises(SomeException):
            with uow:
                insert_batch(uow.session, 'batch1', 'LARGE-FORK', 100, None)
                raise SomeException()

        new_session = postgres_session()
        rows = list(new_session.execute('SELECT * FROM "batches"'))
        new_session.close()
        assert rows == []

    def test_concurrent_updates_to_version_are_not_allowed_returns_ok(self, postgres_session):
        sku, batch = random_sku(), random_batchref()
        session = postgres_session()
        insert_batch(session, batch, sku, 100, eta=None, version=1)
        session.commit()

        order1, order2 = random_orderid(1), random_orderid(2)
        exceptions = []  # type List[Exception]
        try_to_allocate_order1 = lambda: try_to_allocate(order1, sku, exceptions)
        try_to_allocate_order2 = lambda: try_to_allocate(order2, sku, exceptions)
        thread1 = threading.Thread(target=try_to_allocate_order1)
        thread2 = threading.Thread(target=try_to_allocate_order2)
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        # [[]] - unpack value from 2-n dimensional list
        [[version]] = session.execute(
            "SELECT version FROM products WHERE sku=:sku",
            dict(sku=sku),
        )
        assert version == 2  # проверяем, что только одна транзакция изменила версию
        [exception] = exceptions
        assert "could not serialize access due to concurrent update" in str(exception)

        orders = session.execute(
            "SELECT orderid FROM allocations"
            " JOIN batches ON allocations.batch_id = batches.id"
            " JOIN order_lines ON allocations.orderline_id = order_lines.id"
            " WHERE order_lines.sku=:sku",
            dict(sku=sku),
        )
        session.close()
        assert orders.rowcount == 1  # проверяем, что в партии разместился только один заказ
        with unit_of_work.SqlAlchemyUnitOfWork() as uow:
            uow.session.execute("select 1")  # вернет один, если есть запись в таблице
