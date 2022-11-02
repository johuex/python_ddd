import pytest
from models import domain_models, exceptions
from services import allocate_service, repository


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
    def test_returns_allocation(self):
        """
        1. Размещаем в 'БД' партию и товарную позицию на эту партию
        2. Размещаем партию через сервисный слой
        ОР: данные из сервисного слоя совпадают с ожидаемым
        """
        line = domain_models.OrderLine("o1", "COMPLICATED-LAMP", 10)
        batch = domain_models.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
        repo = FakeRepository([batch])

        result = allocate_service.allocate(line, repo, FakeSession())
        assert result == "b1"

    def test_error_for_invalid_sku_allocation(self):
        """
        1. Размещаем в 'БД' партию и товарную позицию на другую партию
        2. Размещаем партию через сервисный слой
        ОР: получаем ошибку, что в 'БД' нет такой партии
        """
        line = domain_models.OrderLine("o1", "NONEXISTENTSKU", 10)
        batch = domain_models.Batch("b1", "AREALSKU", 100, eta=None)
        repo = FakeRepository([batch])

        with pytest.raises(allocate_service.InvalidSku, match="Invalid stock-keeping: NONEXISTENTSKU"):
            allocate_service.allocate(line, repo, FakeSession())

    def test_commits(self):
        """
        1. Размещаем в 'БД' партию и товарную позицию на другую партию
        ОР: commit в 'сессии' == True
        """
        line = domain_models.OrderLine("o1", "OMINOUS-MIRROR", 10)
        batch = domain_models.Batch("b1", "OMINOUS-MIRROR", 100, eta=None)
        repo = FakeRepository([batch])
        session = FakeSession()

        allocate_service.allocate(line, repo, session)
        assert session.committed is True


class TestServiceDeallocation:
    def test_returns_deallocation(self):
        """
        1. Размещаем в 'БД' партию и товарную позицию на эту партию
        2. Размещаем партию через сервисный слой
        3. Отменяем размещение партии через сервисный слой
        ОР: данные из сервисного слоя совпадают с ожидаемым
        """
        line = domain_models.OrderLine("o1", "COMPLICATED-LAMP", 10)
        batch = domain_models.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
        repo = FakeRepository([batch])
        session = FakeSession()

        result = allocate_service.allocate(line, repo, session)
        assert result == "b1"
        result_2 = allocate_service.deallocate(line, repo, session)
        assert result_2 == "b1"

    def test_error_for_invalid_sku_allocation(self):
        """
        1. Размещаем в 'БД' партию и товарную позицию на другую партию
        2. Размещаем партию через сервисный слой
        ОР: получаем ошибку, что в 'БД' нет такой партии
        """
        line_1 = domain_models.OrderLine("o1", "NONEXISTENTSKU", 10)
        line_2 = domain_models.OrderLine("o1", "COMPLICATED-LAMP", 10)
        batch = domain_models.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
        repo = FakeRepository([batch])

        with pytest.raises(exceptions.InvalidSku, match="Invalid stock-keeping: NONEXISTENTSKU"):
            allocate_service.deallocate(line_1, repo, FakeSession())

        with pytest.raises(
                exceptions.NoOrderInBatch,
                #match=f"No order line o1:COMPLICATED-LAMP in batches ['COMPLICATED-LAMP']"
        ):
            allocate_service.deallocate(line_2, repo, FakeSession())
