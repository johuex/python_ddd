"""
Обработчики событий сервисного слоя
"""
from __future__ import annotations  # TODO узнать для чего это

from src.allocation.adapters import email
from src.allocation.entrypoints import redis as redis_entrypoint
from src.allocation.models import domain
from src.allocation.models import events
from src.allocation.models.exceptions import InvalidSku
from src.allocation.services import unit_of_work


def is_valid_sku(sku, batches):
    """
    Check if line.sku exists in some batch
    """
    return sku in {b.sku for b in batches}


def add_batch(event: events.BatchCreated, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get(sku=event.sku)
        if product is None:
            product = domain.Product(event.sku, batches=[])
            uow.products.add(product)
        product.batches.append(domain.Batch(event.ref, event.sku, event.qty, event.eta))
        uow.commit()


def allocate(event: events.AllocationRequired, uow: unit_of_work.AbstractUnitOfWork) -> str:
    """
    то есть зависим от абстракции из принципа инверсии зависимости;
    эта функция сервисного слоя соединяет API и службу предметной области
    """
    line = domain.OrderLine(event.order_id, event.sku, event.qty)
    with uow:
        product = uow.products.get(line.sku)
        if product is None:
            raise InvalidSku(line.sku)
        batchref = product.allocate(line)
        uow.commit()

    return batchref


def deallocate(event: events.DeAllocationRequired, uow: unit_of_work.AbstractUnitOfWork) -> str:
    line = domain.OrderLine(event.order_id, event.sku, event.qty)
    with uow:
        product = uow.products.get(line.sku)
        if product is None:
            raise InvalidSku(line.sku)
        batchref = product.deallocate(line)
        uow.commit()

    return batchref


def send_out_of_stock_notification(event: events.OutOfStock):
    email.send_email('stock@made.com', f'Article {event.sku} is out of stock',)


def change_batch_quantity(event: events.BatchQuantityChanged, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get_by_batchref(batchref=event.ref)
        product.change_batch_quantity(ref=event.ref, qty=event.qty)
        uow.commit()


def publish_allocated_event(event: events.Allocated, uow: unit_of_work.AbstractUnitOfWork):
    redis_entrypoint.publish('line_allocated', event)
