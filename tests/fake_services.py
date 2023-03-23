from typing import List, Dict, Type, Callable

from loguru import logger

from src.allocation.adapters import repository
from src.allocation.models import events, commands
from src.allocation.services import unit_of_work, messagebus


class FakeSession:
    def execute(self, *args, **kwargs):
        pass


class FakeRepository(repository.AbstractRepository):
    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def _add(self, product):
        self._products.add(product)

    def _get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)

    def _get_by_batchref(self, batchref):
        return next((
            p for p in self._products for b in p.batches
            if b.reference == batchref
        ), None)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    session = FakeSession

    def __init__(self):
        self.products = FakeRepository([])  # collaboration of ouw and repo
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


class FakeMessageBus(messagebus.AbstractMessageBus):
    def __init__(
        self,
        uow: unit_of_work.AbstractUnitOfWork,
        event_handlers: Dict[Type[events.Event], List[Callable]],
        command_handlers: Dict[Type[commands.Command], Callable]
    ):
        super().__init__(uow, event_handlers, command_handlers)
        self.message_published = []

    def handle(self, message: messagebus.Message):
        results = []  # results in messagebus from service layer
        queue = [message]  # start queue on first event
        while queue:
            message = queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(message, queue)
            elif isinstance(message, commands.Command):
                cmd_result = self.handle_command(message, queue)
                results.append(cmd_result)
            else:
                raise Exception(f'{message} was not an Event or Command')
        return results

    def handle_event(self, event: events.Event, queue: List[messagebus.Message]):
        logger.debug(f"handling event {event}")
        self.message_published.append(event)
        handlers = self.event_handlers[type(event)]
        for handler in handlers:
            try:
                handler(event)
                queue.extend(self.uow.collect_new_events())
            except Exception:
                logger.exception(f"Exception handling event {event}")
                raise

    def handle_command(self, command: commands.Command, queue: List[messagebus.Message]):
        logger.debug("handling command %s", command)
        try:
            handler = self.command_handlers[type(command)]
            result = handler(command)
            self.message_published.append(command)
            queue.extend(self.uow.collect_new_events())
            return result
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise
