import abc

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.allocation.core import config
from src.allocation.adapters import repository


DEFAULT_SESSION_FACTORY = sessionmaker(bind=create_engine(
    config.get_postgres_uri(),
    isolation_level="REPEATABLE READ"  # уровень изолированности транзакции
))


class AbstractUnitOfWork(abc.ABC):
    products: repository.AbstractRepository  # access to product (bathes with required sku) in repo

    # for contextmanager style
    def __enter__(self, *args):
        return self

    def __exit__(self, *args):  # if only raise Exception
        self.rollback()

    @abc.abstractmethod
    def commit(self):  # fix changes in repo
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory

    def __enter__(self):  # on contextmanager entry; connecting to db and creating copy of real repo
        self.session = self.session_factory()  # type sqla.Session
        self.products = repository.SqlAlchemyRepository(self.session)
        return super().__enter__()

    def __exit__(self, *args): # on contextmanager exit; close session
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
