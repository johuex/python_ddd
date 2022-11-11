import pytest
from models import domain_models, exceptions
from service_layer import allocate_service, batch_service
from adapters import repository


class FakeRepository(repository.AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


class TestServiceAllocation:
    def test_add_batch(self):
        """
        1. Размещаем партию через сервисный слой
        ОР: партия размещена в БД
        """
        repo, session = FakeRepository([]), FakeSession()
        batch_service.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, repo, session)
        assert repo.get("b1") is not None
        assert session.committed

    def test_allocate_returns_allocation(self):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем в партии товарную позицию через сервисный слой
        ОР: товарная позиция разместилась в партии
        """
        repo, session = FakeRepository([]), FakeSession()
        batch_service.add_batch("batch1", "COMPLICATED-LAMP", 100, None, repo, session)
        result = allocate_service.allocate("o1", "COMPLICATED-LAMP", 10, repo, session)
        assert result == "batch1"

    def test_allocate_errors_for_invalid_sku(self):
        """
        1. Размещаем партию с одним артикулом через сервисный слой
        2. Пробуем разместить в партии товарную позицию с другим артикулом через сервисный слой
        ОР: Invalid sku NONEXISTENTSKU, товарная позиция не разместилась в партии
        """
        repo, session = FakeRepository([]), FakeSession()
        batch_service.add_batch("b1", "AREALSKU", 100, None, repo, session)

        with pytest.raises(allocate_service.InvalidSku, match="Invalid stock-keeping: NONEXISTENTSKU"):
            allocate_service.allocate("o1", "NONEXISTENTSKU", 10, repo, FakeSession())

    def test_commits(self):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем в партии товарную позицию через сервисный слой
        ОР: товарная позиция разместилась в партии, изменения committed в сессии
        """
        repo, session = FakeRepository([]), FakeSession()
        batch_service.add_batch("b1", "OMINOUS-MIRROR", 100, None, repo, session)
        allocate_service.allocate("o1", "OMINOUS-MIRROR", 10, repo, session)
        assert session.committed is True


class TestServiceDeallocation:
    def test_returns_deallocation(self):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем товарную позицию на эту партию через сервисный слой
        3. Отменяем размещение партии через сервисный слой
        ОР: данные из сервисного слоя совпадают с ожидаемым
        """
        repo, session = FakeRepository([]), FakeSession()
        batch_service.add_batch("b1", "COMPLICATED-LAMP", 100, None, repo, session)
        result = allocate_service.allocate("o1", "COMPLICATED-LAMP", 10, repo, session)

        assert result == "b1"
        result_2 = allocate_service.deallocate("o1", "COMPLICATED-LAMP", 10, repo, session)
        assert result_2 == "b1"

    def test_error_for_invalid_sku_allocation(self):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем товарную позицию через сервисный слой
        3. Отменяем товарную позицию с другим артикулом
        ОР: получаем ошибку, что нет такой партии
        """
        repo, session = FakeRepository([]), FakeSession()
        batch_service.add_batch("b1", "COMPLICATED-LAMP", 100, None, repo, session)
        with pytest.raises(exceptions.InvalidSku, match="Invalid stock-keeping: NONEXISTENTSKU"):
            allocate_service.deallocate("o1", "NONEXISTENTSKU", 10, repo, session)
        with pytest.raises(
                exceptions.NoOrderInBatch,
                #match=f"No order line o1:COMPLICATED-LAMP in batches ['COMPLICATED-LAMP']"
        ):
            allocate_service.deallocate("o1", "COMPLICATED-LAMP", 10, repo, session)
