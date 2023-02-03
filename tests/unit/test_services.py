import pytest
from src.allocation.models import exceptions
from src.allocation.services import allocate_service, unit_of_work
from src.allocation.services import batch_service
from src.allocation.adapters import repository


class FakeRepository(repository.AbstractRepository):
    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def _add(self, product):
        self._products.add(product)

    def _get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])  # collaboration of ouw and repo
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


class TestServiceAllocation:
    def test_add_batch(self):
        """
        1. Размещаем партию через сервисный слой
        ОР: партия размещена в БД
        """
        uow = FakeUnitOfWork()
        batch_service.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
        assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert uow.committed

    def test_allocate_returns_allocation(self):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем в партии товарную позицию через сервисный слой
        ОР: товарная позиция разместилась в партии
        """
        uow = FakeUnitOfWork()
        batch_service.add_batch("batch1", "COMPLICATED-LAMP", 100, None, uow)
        result = allocate_service.allocate("o1", "COMPLICATED-LAMP", 10, uow)
        assert result == "batch1"

    def test_allocate_errors_for_invalid_sku(self):
        """
        1. Размещаем партию с одним артикулом через сервисный слой
        2. Пробуем разместить в партии товарную позицию с другим артикулом через сервисный слой
        ОР: Invalid sku NONEXISTENTSKU, товарная позиция не разместилась в партии
        """
        uow = FakeUnitOfWork()
        batch_service.add_batch("b1", "AREALSKU", 100, None, uow)

        with pytest.raises(allocate_service.InvalidSku, match="Invalid stock-keeping: NONEXISTENTSKU"):
            allocate_service.allocate("o1", "NONEXISTENTSKU", 10, uow)

    def test_commits(self):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем в партии товарную позицию через сервисный слой
        ОР: товарная позиция разместилась в партии, изменения committed в сессии
        """
        uow = FakeUnitOfWork()
        batch_service.add_batch("b1", "OMINOUS-MIRROR", 100, None, uow)
        allocate_service.allocate("o1", "OMINOUS-MIRROR", 10, uow)
        assert uow.committed is True


class TestServiceDeallocation:
    def test_returns_deallocation(self):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем товарную позицию на эту партию через сервисный слой
        3. Отменяем размещение партии через сервисный слой
        ОР: данные из сервисного слоя совпадают с ожидаемым
        """
        uow = FakeUnitOfWork()
        batch_service.add_batch("b1", "COMPLICATED-LAMP", 100, None, uow)
        result = allocate_service.allocate("o1", "COMPLICATED-LAMP", 10, uow)

        assert result == "b1"
        result_2 = allocate_service.deallocate("o1", "COMPLICATED-LAMP", 10, uow)
        assert result_2 == "b1"

    def test_error_for_invalid_sku_allocation(self):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем товарную позицию через сервисный слой
        3. Отменяем товарную позицию с другим артикулом
        ОР: получаем ошибку, что нет такой партии
        """
        uow = FakeUnitOfWork()
        batch_service.add_batch("b1", "COMPLICATED-LAMP", 100, None, uow)
        with pytest.raises(exceptions.InvalidSku, match="Invalid stock-keeping: NONEXISTENTSKU"):
            allocate_service.deallocate("o1", "NONEXISTENTSKU", 10, uow)
        with pytest.raises(
                exceptions.NoOrderInBatch,
                #match=f"No order line o1:COMPLICATED-LAMP in batches ['COMPLICATED-LAMP']"
        ):
            allocate_service.deallocate("o1", "COMPLICATED-LAMP", 10, uow)
