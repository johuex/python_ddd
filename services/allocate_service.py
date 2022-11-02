"""
Здесь будут лежать функции службы
"""
from __future__ import annotations  # TODO узнать для чего это

from models import domain_models
from models.domain_models import OrderLine
from models.exceptions import InvalidSku
from services.repository import AbstractRepository


def is_valid_sku(sku, batches):
    """
    Check if line.sku exists in some batch
    """
    return sku in {b.sku for b in batches}


def allocate(line: OrderLine, repo: AbstractRepository, session) -> str:
    """
    repo: AbstractRepository позволяет использовать как FakeRepository, так и SqlAlchemyRepository,
    то есть зависим от абстракции из принципа инверсии зависимости;
    эта функция сервисного слоя соединяет API и службу предметной области
    """
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(line.sku)
    batchref = domain_models.allocate(line, batches)
    session.commit()
    return batchref


def deallocate(line: OrderLine, repo: AbstractRepository, session) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(line.sku)
    batchref = domain_models.deallocate(line, batches)
    session.commit()
    return batchref
