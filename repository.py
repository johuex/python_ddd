import abc

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import domain_models


class AbstractRepository(abc.ABC):
    """
    Абстрактный класс-родитель для последующих репозиториев ниже
    """
    @abc.abstractmethod
    def add(self, batch: domain_models.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> domain_models.Batch:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    """
    Репозиторий для реального использования
    """
    def __init__(self, session: Session):
        self.session = session

    def add(self, batch: domain_models.Batch):
        self.session.add(batch)

    def get(self, reference) -> domain_models.Batch:
        res = self.session.execute(
            select(domain_models.Batch).where(domain_models.Batch.reference == reference)
        ).scalar_one_or_none()

        return res
