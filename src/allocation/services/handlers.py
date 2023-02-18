"""
Обработчики событий сервисного слоя
"""
from __future__ import annotations  # TODO узнать для чего это

from dataclasses import asdict

from src.allocation.adapters import email
from src.allocation.entrypoints import redis_mbus as redis_entrypoint
from src.allocation.models import domain, commands
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


def reallocate(
    event: events.Deallocated,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get(sku=event.sku)
        product.events.append(commands.Allocate(**asdict(event)))
        uow.commit()


def send_out_of_stock_notification(event: events.OutOfStock):
    email.send_email('stock@made.com', f'Article {event.sku} is out of stock',)


def change_batch_quantity(event: events.BatchQuantityChanged, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get_by_batchref(batchref=event.ref)
        product.change_batch_quantity(ref=event.ref, qty=event.qty)
        uow.commit()


def publish_allocated_event(event: events.Allocated, uow: unit_of_work.AbstractUnitOfWork):
    redis_entrypoint.publish('line_allocated', event)


def add_allocation_to_read_model(
    event: events.Allocated,
    uow: unit_of_work.SqlAlchemyUnitOfWork,
):
    with uow:
        uow.session.execute(
            'INSERT INTO allocations_view (order_id, sku, batchref)'
            ' VALUES (:order_id, :sku, :batchref)',
            dict(order_id=event.order_id, sku=event.sku, batchref=event.batchref)
        )
        uow.commit()


def remove_allocation_from_read_model(
    event: events.Deallocated, uow:
    unit_of_work.SqlAlchemyUnitOfWork,
):
    with uow:
        uow.session.execute(
            'DELETE FROM allocations_view '
            ' WHERE order_id = :order_id AND sku = :sku',
            dict(order_id=event.order_id, sku=event.sku)
        )

        uow.commit()
