import pytest
from models import domain_models
import repository
from services import allocate_service


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


class TestService:
    def test_returns_allocation(self):
        """
        1. Размещаем в 'БД' партию и товарную позицию на эту партию
        2. Получаем партию через сервисный слой
        ОР: данные из сервисного слоя совпадают с ожидаемым
        """
        line = domain_models.OrderLine("o1", "COMPLICATED-LAMP", 10)
        batch = domain_models.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
        repo = FakeRepository([batch])

        result = allocate_service.allocate(line, repo, FakeSession())
        assert result == "b1"


    def test_error_for_invalid_sku(self):
        """
        1. Размещаем в 'БД' партию и товарную позицию на другую партию
        2. Получаем партию через сервисный слой
        ОР: получаем ошибку, что в 'БД' нет такой партии
        """
        line = domain_models.OrderLine("o1", "NONEXISTENTSKU", 10)
        batch = domain_models.Batch("b1", "AREALSKU", 100, eta=None)
        repo = FakeRepository([batch])

        with pytest.raises(allocate_service.InvalidSku, match="Недопустимый артикул: NONEXISTENTSKU"):
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
