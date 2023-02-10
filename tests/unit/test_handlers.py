from datetime import date
from typing import List

import pytest
from loguru import logger

from src.allocation.models import exceptions, events, commands
from src.allocation.services import handlers, unit_of_work, messagebus
from src.allocation.adapters import repository
from src.allocation.services.messagebus import MessageBus, Message


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
    def __init__(self):
        self.products = FakeRepository([])  # collaboration of ouw and repo
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


class FakeMessageBus(messagebus.AbstractMessageBus):
    def __init__(self):
        super().__init__()
        self.command_published = []
        self.command_handlers = {
            commands.Allocate: handlers.allocate,
            commands.CreateBatch: handlers.add_batch,
            commands.ChangeBatchQuantity: handlers.change_batch_quantity,
            commands.Deallocate: handlers.deallocate
        }
        self.event_handlers = {
            events.OutOfStock: [handlers.send_out_of_stock_notification],
        }

    def handle(self, message: Message, uow: unit_of_work.AbstractUnitOfWork):
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

    def handle_command(self, command: commands.Command, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork):
        logger.debug("handling command %s", command)
        try:
            handler = self.command_handlers[type(command)]
            result = handler(command, uow=uow)
            queue.extend(uow.collect_new_events())
            self.command_published.append(command)
            return result
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise

    def handle_event(self, event: events.Event, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork):
        logger.debug("handling event %s", event)
        try:
            handler = self.event_handlers[type(event)]
            result = handler(event, uow=uow)
            queue.extend(uow.collect_new_events())
            return result
        except Exception:
            logger.exception("Exception handling event %s", event)
            raise


class TestAllocationRequired:
    def test_add_batch(self):
        """
        1. Размещаем партию через сервисный слой
        ОР: партия размещена в БД
        """
        uow = FakeUnitOfWork()
        mbus = MessageBus()
        mbus.handle(commands.CreateBatch("b1", "CRUNCHY-ARMCHAIR", 100, None), uow)
        assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert uow.committed

    def test_allocate_returns_allocation(self):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем в партии товарную позицию через сервисный слой
        ОР: товарная позиция разместилась в партии
        """
        uow = FakeUnitOfWork()
        mbus = MessageBus()
        mbus.handle(commands.CreateBatch("batch1", "COMPLICATED-LAMP", 100, None), uow)
        result = mbus.handle(commands.Allocate("o1", "COMPLICATED-LAMP", 10), uow)
        assert result.pop(0) == "batch1"

    def test_allocate_errors_for_invalid_sku(self):
        """
        1. Размещаем партию с одним артикулом через сервисный слой
        2. Пробуем разместить в партии товарную позицию с другим артикулом через сервисный слой
        ОР: Invalid sku NONEXISTENTSKU, товарная позиция не разместилась в партии
        """
        uow = FakeUnitOfWork()
        mbus = MessageBus()
        mbus.handle(commands.CreateBatch("b1", "AREALSKU", 100, None), uow)

        with pytest.raises(handlers.InvalidSku, match="Invalid stock-keeping: NONEXISTENTSKU"):
            mbus.handle(commands.Allocate("o1", "NONEXISTENTSKU", 10), uow)

    def test_commits(self):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем в партии товарную позицию через сервисный слой
        ОР: товарная позиция разместилась в партии, изменения committed в сессии
        """
        uow = FakeUnitOfWork()
        mbus = MessageBus()
        mbus.handle(commands.CreateBatch("b1", "OMINOUS-MIRROR", 100, None), uow)
        mbus.handle(commands.Allocate("o1", "OMINOUS-MIRROR", 10), uow)
        assert uow.committed is True


class TestDeallocationRequired:
    def test_returns_deallocation(self):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем товарную позицию на эту партию через сервисный слой
        3. Отменяем размещение партии через сервисный слой
        ОР: данные из сервисного слоя совпадают с ожидаемым
        """
        uow = FakeUnitOfWork()
        mbus = MessageBus()
        mbus.handle(commands.CreateBatch("b1", "COMPLICATED-LAMP", 100, None), uow)
        result = mbus.handle(commands.Allocate("o1", "COMPLICATED-LAMP", 10), uow)

        assert result.pop(0) == "b1"
        result_2 = mbus.handle(commands.Deallocate("o1", "COMPLICATED-LAMP", 10), uow)
        assert result_2.pop(0) == "b1"

    def test_error_for_invalid_sku_allocation(self):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем товарную позицию через сервисный слой
        3. Отменяем товарную позицию с другим артикулом
        ОР: получаем ошибку, что нет такой партии
        """
        uow = FakeUnitOfWork()
        mbus = MessageBus()
        mbus.handle(commands.CreateBatch("b1", "COMPLICATED-LAMP", 100, None), uow)
        with pytest.raises(exceptions.InvalidSku, match="Invalid stock-keeping: NONEXISTENTSKU"):
            mbus.handle(commands.Allocate("o1", "NONEXISTENTSKU", 10), uow)
        with pytest.raises(
                exceptions.NoOrderInBatch,
                #match=f"No order line o1:COMPLICATED-LAMP in batches ['COMPLICATED-LAMP']"
        ):
            mbus.handle(commands.Deallocate("o1", "COMPLICATED-LAMP", 10), uow)


class TestChangeBatchQuantity:
    def test_changes_available_quantity(self):
        """
        1. Создаем партию
        2. Меняем кол-во доступнх товар в партии

        ОР: кол-во доступных товаров в партии изменилось
        """
        uow = FakeUnitOfWork()

        mbus = MessageBus()
        mbus.handle(
            commands.CreateBatch("batch1", "ADORABLE-SETTEE", 100,
                                None), uow
        )
        [batch] = uow.products.get(sku="ADORABLE-SETTEE").batches
        assert batch.available_quantity == 100
        mbus.handle(commands.ChangeBatchQuantity("batch1", 50), uow)
        assert batch.available_quantity == 50

    def test_reallocates_if_necessary(self):
        """
        1. Создаем две партии
        2. Пытаемся разместить два заказа, оба уходят в раннюю партию
        3. Меняем размер ранней партии так, чтобы отменился один из заказов

        ОР: один из заказов отменился и разместился в другой партии
        """
        uow = FakeUnitOfWork()
        mbus = MessageBus()

        event_history = [
            commands.CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
            commands.CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            commands.Allocate("order1", "INDIFFERENT-TABLE", 20),
            commands.Allocate("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            mbus.handle(e, uow)

        [batch1, batch2] = uow.products.get(sku="INDIFFERENT-TABLE").batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50
        mbus.handle(commands.ChangeBatchQuantity("batch1", 25), uow)
        # размещение заказа order1 или order2 будет отменено, и у нас
        # будет 25 - 20
        assert batch1.available_quantity == 5
        # и 20 будет повторно размещено в следующей партии
        assert batch2.available_quantity == 30

    def test_reallocates_if_necessary_isolated(self):
        uow = FakeUnitOfWork()
        mbus = FakeMessageBus()
        # тестовые условия, как и раньше
        event_history = [
            commands.CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
            commands.CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            commands.Allocate("order1", "INDIFFERENT-TABLE", 20),
            commands.Allocate("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            mbus.handle(e, uow)
        [batch1, batch2] = uow.products.get(sku="INDIFFERENT-TABLE").batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50
        mbus.handle(commands.ChangeBatchQuantity("batch1", 25), uow)
        # подтвердить истинность на новых порожденных событиях,
        # а не на последующих побочных эффектах
        reallocation_command = mbus.command_published[-1]
        assert isinstance(reallocation_command, commands.Allocate)
        assert reallocation_command.order_id in {'order1', 'order2'}
        assert reallocation_command.sku == 'INDIFFERENT-TABLE'
