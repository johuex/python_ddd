import abc
from typing import Dict, Type, List, Callable, Union

from loguru import logger
from tenacity import Retrying, stop_after_attempt, wait_exponential, RetryError

from src.allocation.models import events, commands
from src.allocation.services import unit_of_work
from src.allocation.services import handlers


Message = Union[commands.Command, events.Event]


class AbstractMessageBus(abc.ABC):
    EVENT_HANDLERS: Dict[Type[events.Event], List[Callable]]
    COMMAND_HANDLERS: Dict[Type[events.Event], List[Callable]]

    @abc.abstractmethod
    def handle(self, message: Message, uow: unit_of_work.AbstractUnitOfWork):
        raise NotImplementedError

    @abc.abstractmethod
    def handle_event(self, event: events.Event, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork):
        raise NotImplementedError

    @abc.abstractmethod
    def handle_command(self, command: commands.Command, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork):
        raise NotImplementedError


class MessageBus(AbstractMessageBus):
    EVENT_HANDLERS = {
        events.OutOfStock: [handlers.send_out_of_stock_notification],
    }

    COMMAND_HANDLERS = {
        commands.Allocate: handlers.allocate,
        commands.CreateBatch: handlers.add_batch,
        commands.ChangeBatchQuantity: handlers.change_batch_quantity,
        commands.Deallocate: handlers.deallocate
    }

    def handle(self, message: Message, uow: unit_of_work.AbstractUnitOfWork):
        # Now UoW goes through the message bus on every uow start
        results = []  # results in messagebus from service layer
        queue = [message]  # start queue on first event
        while queue:
            message = queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(message, queue, uow)
            elif isinstance(message, commands.Command):
                cmd_result = self.handle_command(message, queue, uow)
                results.append(cmd_result)
            else:
                raise Exception(f'{message} was not an Event or Command')
        return results

    def handle_event(self, event: events.Event, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork):
        for handler in self.EVENT_HANDLERS[type(event)]:
            try:
                for attempt in Retrying(
                    stop=stop_after_attempt(3),  # retry for 3 times
                    wait=wait_exponential() # exponential timeout between attempts
                ):
                    with attempt:
                        logger.debug('handling event %s with handler %s', event, handler)
                        handler(event, uow=uow)
                        queue.extend(uow.collect_new_events())
            except RetryError as retry_failure:
                # logging error, but not interrupting message processing
                logger.error('Exception handling event %s', event)
                continue

    def handle_command(self, command: commands.Command, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork):
        logger.debug('handling command %s', command)
        try:
            handler = self.COMMAND_HANDLERS[type(command)]
            result = handler(command, uow=uow)
            queue.extend(uow.collect_new_events())
            return result  # TODO костыль
        except Exception:
            logger.error('Exception handling command %s', command)
            raise
