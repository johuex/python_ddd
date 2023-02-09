import abc

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.allocation.models import domain


class AbstractRepository(abc.ABC):
    """
    Абстрактный класс-родитель для последующих репозиториев ниже
    """
    def __init__(self):
        self.seen = set()  # type Set[model.Product]; объекты, которые испол-сь во время сеанса

    def add(self, product: domain.Product):
        self._add(product)
        self.seen.add(product)

    def get(self, sku) -> domain.Product:
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    def get_by_batchref(self, batchref) -> domain.Product:
        product = self._get_by_batchref(batchref)
        if product:
            self.seen.add(product)
        return product

    @abc.abstractmethod
    def _add(self, product: domain.Product):
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, sku) -> domain.Product:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_by_batchref(self, batchref) -> domain.Product:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    """
    Репозиторий для реального использования
    """
    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    def _add(self, product: domain.Product):
        self.session.add(product)

    def _get(self, sku) -> domain.Product:
        res = self.session.execute(
            select(domain.Product).where(domain.Product.sku == sku)
        ).scalars().first()

        return res

    def _get_by_batchref(self, batchref) -> domain.Product:
        res = self.session.execute(
            select(domain.Product).join(domain.Batch).where(domain.Batch.reference == batchref)
        ).scalars().first()

        return res
