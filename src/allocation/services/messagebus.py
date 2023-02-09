from typing import Dict, Type, List, Callable

from src.allocation.models import events
from src.allocation.services import unit_of_work
from src.allocation.services import handlers


class AbstractMessageBus:
    HANDLERS: Dict[Type[events.Event], List[Callable]]

    def handle(self, event: events.Event, uow: unit_of_work.AbstractUnitOfWork):
        for handler in self.HANDLERS[type(event)]:
            handler(event, uow)


class MessageBus(AbstractMessageBus):
    HANDLERS = {
        events.BatchCreated: [handlers.add_batch],
        events.AllocationRequired: [handlers.allocate],
        events.OutOfStock: [handlers.send_out_of_stock_notification],
        events.DeAllocationRequired: [handlers.deallocate],
        events.BatchQuantityChanged: [handlers.change_batch_quantity]
    }

    def handle(self, event: events.Event, uow: unit_of_work.AbstractUnitOfWork):
        # Now UoW goes through the message bus on every uow start
        results = []  # results in messagebus from service layer
        queue = [event]  # start queue on first event
        while queue:
            event = queue.pop(0)
            for handler in self.HANDLERS[type(event)]:
                results.append(handler(event, uow=uow))  # messagebus gives uow to next handler
                queue.extend(uow.collect_new_events())  # collect new events, add them to queue
        return results



