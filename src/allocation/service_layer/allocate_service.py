"""
Здесь будут лежать функции службы (de-)allocate
"""
from __future__ import annotations  # TODO узнать для чего это

from src.allocation.models.domain_models import OrderLine
from src.allocation.models.exceptions import InvalidSku
from src.allocation.service_layer import unit_of_work


def is_valid_sku(sku, batches):
    """
    Check if line.sku exists in some batch
    """
    return sku in {b.sku for b in batches}


def allocate(orderid: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork) -> str:
    """
    то есть зависим от абстракции из принципа инверсии зависимости;
    эта функция сервисного слоя соединяет API и службу предметной области
    """
    line = OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(line.sku)
        if product is None:
            raise InvalidSku(line.sku)
        batchref = product.allocate(line)
        uow.commit()

    return batchref


def deallocate(orderid: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(line.sku)
        if product is None:
            raise InvalidSku(line.sku)
        batchref = product.deallocate(line)
        uow.commit()

    return batchref
