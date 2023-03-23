from typing import Callable, Type

from src.allocation.adapters import orm
from src.allocation.adapters import notifications
from src.allocation.adapters import redis_event_publisher
from src.allocation.core.config import app_settings
from src.allocation.models import events, commands
from src.allocation.services import unit_of_work, messagebus, handlers


def bootstrap(
    start_orm: bool = True,
    uow: unit_of_work.AbstractUnitOfWork = unit_of_work.SqlAlchemyUnitOfWork(),
    notification: notifications.AbstractNotification = notifications.EmailNotification(),
    publish: Callable = redis_event_publisher.publish,
    message_bus: Type[messagebus.AbstractMessageBus] = messagebus.MessageBus
) -> messagebus.AbstractMessageBus:
    """
    Production Use Bootstrap
    """
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
            handlers.SendOutOfStackNotificationHandler(notification)
        ]
    }
    injected_command_handlers = {
        commands.Allocate: handlers.AllocateHandler(uow),
        commands.Deallocate: handlers.DeAllocateHandler(uow),
        commands.CreateBatch: handlers.AddBatchHandler(uow),
        commands.ChangeBatchQuantity: handlers.ChangeBatchQuantityHandler(uow),
    }

    return message_bus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )


if app_settings.bus_init_need:
    bus = bootstrap()
