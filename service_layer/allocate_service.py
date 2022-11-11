"""
Здесь будут лежать функции службы (de-)allocate
"""
from __future__ import annotations  # TODO узнать для чего это

from models import domain_models
from models.domain_models import OrderLine
from models.exceptions import InvalidSku
from adapters.repository import AbstractRepository


def is_valid_sku(sku, batches):
    """
    Check if line.sku exists in some batch
    """
    return sku in {b.sku for b in batches}


def allocate(orderid: str, sku: str, qty: int, repo: AbstractRepository, session) -> str:
    """
    repo: AbstractRepository позволяет использовать как FakeRepository, так и SqlAlchemyRepository,
    то есть зависим от абстракции из принципа инверсии зависимости;
    эта функция сервисного слоя соединяет API и службу предметной области
    """
    line = OrderLine(orderid, sku, qty)
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(line.sku)
    batchref = domain_models.allocate(line, batches)
    session.commit()
    return batchref


def deallocate(orderid: str, sku: str, qty: int, repo: AbstractRepository, session) -> str:
    line = OrderLine(orderid, sku, qty)
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(line.sku)
    batchref = domain_models.deallocate(line, batches)
    session.commit()
    return batchref
