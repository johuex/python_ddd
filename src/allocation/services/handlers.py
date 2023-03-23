"""
Обработчики событий сервисного слоя
"""
from __future__ import annotations  # TODO узнать для чего это

import abc
from dataclasses import asdict
from typing import Any, Callable

from src.allocation.adapters import notifications
from src.allocation.models import domain, commands
from src.allocation.models import events
from src.allocation.models.exceptions import InvalidSku
from src.allocation.models.messages import Message
from src.allocation.services import unit_of_work


class AbstractHandler(abc.ABC):
    def __init__(self, uow: unit_of_work.AbstractUnitOfWork) -> None:
        self.uow = uow

    @abc.abstractmethod
    def __call__(self, message: Message, *args, **kwargs) -> Any:
        raise NotImplementedError


class AddBatchHandler(AbstractHandler):
    def __call__(self, event: events.BatchCreated, *args, **kwargs) -> None:
        with self.uow:
            product = self.uow.products.get(sku=event.sku)
            if product is None:
                product = domain.Product(event.sku, batches=[])
                self.uow.products.add(product)
            product.batches.append(domain.Batch(event.ref, event.sku, event.qty, event.eta))
            self.uow.commit()


class AllocateHandler(AbstractHandler):
    def __call__(self, event: events.AllocationRequired, *args, **kwargs) -> str:
        line = domain.OrderLine(event.order_id, event.sku, event.qty)
        with self.uow:
            product = self.uow.products.get(line.sku)
            if product is None:
                raise InvalidSku(line.sku)
            batchref = product.allocate(line)
            self.uow.commit()

        return batchref


class DeAllocateHandler(AbstractHandler):
    def __call__(self, event: events.DeAllocationRequired, *args, **kwargs) -> str:
        line = domain.OrderLine(event.order_id, event.sku, event.qty)
        with self.uow:
            product = self.uow.products.get(line.sku)
            if product is None:
                raise InvalidSku(line.sku)
            batchref = product.deallocate(line)
            self.uow.commit()

        return batchref


class ReAllocateHandler(AbstractHandler):
    def __call__(self, event: events.Deallocated, *args, **kwargs):
        with self.uow:
            product = self.uow.products.get(sku=event.sku)
            product.events.append(commands.Allocate(**asdict(event)))
            self.uow.commit()


class ChangeBatchQuantityHandler(AbstractHandler):
    def __call__(self, event: events.BatchQuantityChanged, *args, **kwargs):
        with self.uow:
            product = self.uow.products.get_by_batchref(batchref=event.ref)
            product.change_batch_quantity(ref=event.ref, qty=event.qty)
            self.uow.commit()


class AddAllocationToViewHandler(AbstractHandler):
    def __init__(self, uow: unit_of_work.SqlAlchemyUnitOfWork) -> None:
        super().__init__(uow)
        self.uow = uow

    def __call__(self, event: events.Allocated, *args, **kwargs):
        with self.uow:
            self.uow.session.execute(
                'INSERT INTO allocations_view (order_id, sku, batchref)'
                ' VALUES (:order_id, :sku, :batchref)',
                dict(order_id=event.order_id, sku=event.sku, batchref=event.batchref)
            )
            self.uow.commit()


class RemoveAllocationFromView(AbstractHandler):
    def __init__(self, uow: unit_of_work.SqlAlchemyUnitOfWork) -> None:
        super().__init__(uow)
        self.uow = uow

    def __call__(self, event: events.Deallocated, *args, **kwargs):
        with self.uow:
            self.uow.session.execute(
                'DELETE FROM allocations_view '
                ' WHERE order_id = :order_id AND sku = :sku',
                dict(order_id=event.order_id, sku=event.sku)
            )

            self.uow.commit()


class SendOutOfStackNotificationHandler:
    def __init__(self, notification: notifications.AbstractNotification) -> None:
        self.notification = notification

    def __call__(self, event: events.OutOfStock, *args, **kwargs):
        self.notification.send('stock@made.com', f'Article {event.sku} is out of stock')


class PublishAllocatedEventHandler:
    def __init__(self, redis_publish: Callable):
        self.redis_publish = redis_publish

    def __call__(self, event: events.Allocated, *args, **kwargs):
        self.redis_publish('line_allocated', event)
