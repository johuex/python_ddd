import abc
from typing import Dict, Type, List, Callable

from loguru import logger
from tenacity import Retrying, stop_after_attempt, wait_exponential, RetryError

from src.allocation.models import events, commands
from src.allocation.models.messages import Message
from src.allocation.services import unit_of_work


class AbstractMessageBus(abc.ABC):
    # a predefined list of not injected handlers and command for each type of messagebus
    def __init__(
        self,
        uow: unit_of_work.AbstractUnitOfWork,
        event_handlers: Dict[Type[events.Event], List[Callable]],
        command_handlers: Dict[Type[commands.Command], Callable]
    ):
        """
        Init messagebus with injected handlers and commands +  required unit_of_work
        """
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    @abc.abstractmethod
    def handle(self, message: Message):
        raise NotImplementedError

    @abc.abstractmethod
    def handle_event(self, event: events.Event, queue: List[Message]):
        raise NotImplementedError

    @abc.abstractmethod
    def handle_command(self, command: commands.Command, queue: List[Message]):
        raise NotImplementedError


class MessageBus(AbstractMessageBus):
    def handle(self, message: Message):
        # Now UoW goes through the message bus on every uow start
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

    def handle_event(self, event: events.Event, queue: List[Message]):
        for handler in self.event_handlers[type(event)]:
            try:
                for attempt in Retrying(
                    stop=stop_after_attempt(3),  # retry for 3 times
                    wait=wait_exponential()  # exponential timeout between attempts
                ):
                    with attempt:
                        logger.debug(f'Handling event {event} with handler {handler}')
                        handler(event)
                        queue.extend(self.uow.collect_new_events())
            except RetryError:
                # logging error, but not interrupting message processing
                logger.error(f'Exception handling event {event}')
                continue

    def handle_command(self, command: commands.Command, queue: List[Message]):
        logger.debug(f'Handling command {command}')
        try:
            handler = self.command_handlers[type(command)]
            result = handler(command)
            queue.extend(self.uow.collect_new_events())
            return result  # TODO костыль
        except Exception:
            logger.error(f'Exception handling command {command}')
            raise
