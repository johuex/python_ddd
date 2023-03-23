from typing import Callable

from src.allocation.adapters import orm
from src.allocation.adapters.notifications import AbstractNotification, EmailNotification
from src.allocation.adapters import redis_event_publisher
from src.allocation.models import events, commands
from src.allocation.services import unit_of_work, messagebus, handlers


def bootstrap(
    start_orm: bool = True,
    uow: unit_of_work.AbstractUnitOfWork = unit_of_work.SqlAlchemyUnitOfWork(),
    notifications: AbstractNotification = None,
    publish: Callable = redis_event_publisher.publish,
) -> messagebus.MessageBus:
    """
    Production Use Bootstrap
    """
    if notifications is None:
        notifications = EmailNotification()

    if start_orm:
        orm.start_mappers()

    # FOR PRODUCTION USE
    injected_event_handlers = {
        events.Allocated: [
            handlers.PublishAllocatedEventHandler(publish),
            handlers.AddAllocationToViewHandler(uow),
        ],
        events.Deallocated: [
            handlers.RemoveAllocationFromView(uow),
            handlers.ReAllocateHandler(uow),
        ],
        events.OutOfStock: [
            handlers.SendOutOfStackNotificationHandler(notifications)
        ]
    }
    injected_command_handlers = {
        commands.Allocate: handlers.AllocateHandler(uow),
        commands.CreateBatch: handlers.AddBatchHandler(uow),
        commands.ChangeBatchQuantity: handlers.ChangeBatchQuantityHandler(uow),
    }

    return messagebus.MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )


bus = bootstrap()
