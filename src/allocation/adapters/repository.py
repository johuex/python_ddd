import abc

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.allocation.models import domain_models


class AbstractRepository(abc.ABC):
    """
    Абстрактный класс-родитель для последующих репозиториев ниже
    """
    @abc.abstractmethod
    def add(self, product: domain_models.Product):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, sku) -> domain_models.Product:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    """
    Репозиторий для реального использования
    """
    def __init__(self, session: Session):
        self.session = session

    def add(self, product: domain_models.Product):
        self.session.add(product)

    def get(self, sku) -> domain_models.Product:
        res = self.session.execute(
            select(domain_models.Product).where(domain_models.Product.sku == sku)
        ).scalars().first()

        return res
