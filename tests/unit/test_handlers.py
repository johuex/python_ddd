from datetime import date

import pytest

from src.allocation.models import exceptions, events, commands
from src.allocation.models.exceptions import InvalidSku


class TestAllocationRequired:
    def test_add_batch(self, fake_bus):
        """
        1. Размещаем партию через сервисный слой
        ОР: партия размещена в БД
        """
        mbus = fake_bus
        mbus.handle(commands.CreateBatch("b1", "CRUNCHY-ARMCHAIR", 100, None))
        assert mbus.uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert mbus.uow.committed

    def test_allocate_returns_allocation(self, fake_bus):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем в партии товарную позицию через сервисный слой
        ОР: товарная позиция разместилась в партии
        """
        mbus = fake_bus
        mbus.handle(commands.CreateBatch("batch1", "COMPLICATED-LAMP", 100, None))
        result = mbus.handle(commands.Allocate("o1", "COMPLICATED-LAMP", 10))
        assert result.pop(0) == "batch1"

    def test_allocate_errors_for_invalid_sku(self, fake_bus):
        """
        1. Размещаем партию с одним артикулом через сервисный слой
        2. Пробуем разместить в партии товарную позицию с другим артикулом через сервисный слой
        ОР: Invalid sku NONEXISTENTSKU, товарная позиция не разместилась в партии
        """
        mbus = fake_bus
        mbus.handle(commands.CreateBatch("b1", "AREALSKU", 100, None))

        with pytest.raises(InvalidSku, match="Invalid stock-keeping: NONEXISTENTSKU"):
            mbus.handle(commands.Allocate("o1", "NONEXISTENTSKU", 10))

    def test_commits(self, fake_bus):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем в партии товарную позицию через сервисный слой
        ОР: товарная позиция разместилась в партии, изменения committed в сессии
        """
        mbus = fake_bus
        mbus.handle(commands.CreateBatch("b1", "OMINOUS-MIRROR", 100, None))
        mbus.handle(commands.Allocate("o1", "OMINOUS-MIRROR", 10))
        assert mbus.uow.committed is True


class TestDeallocationRequired:
    def test_returns_deallocation(self, fake_bus):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем товарную позицию на эту партию через сервисный слой
        3. Отменяем размещение партии через сервисный слой
        ОР: данные из сервисного слоя совпадают с ожидаемым
        """
        mbus = fake_bus
        mbus.handle(commands.CreateBatch("b1", "COMPLICATED-LAMP", 100, None))
        result = mbus.handle(commands.Allocate("o1", "COMPLICATED-LAMP", 10))

        assert result.pop(0) == "b1"
        result_2 = mbus.handle(commands.Deallocate("o1", "COMPLICATED-LAMP", 10))
        assert result_2.pop(0) == "b1"

    def test_error_for_invalid_sku_allocation(self, fake_bus):
        """
        1. Размещаем партию через сервисный слой
        2. Размещаем товарную позицию через сервисный слой
        3. Отменяем товарную позицию с другим артикулом
        ОР: получаем ошибку, что нет такой партии
        """
        mbus = fake_bus
        mbus.handle(commands.CreateBatch("b1", "COMPLICATED-LAMP", 100, None))
        with pytest.raises(exceptions.InvalidSku, match="Invalid stock-keeping: NONEXISTENTSKU"):
            mbus.handle(commands.Allocate("o1", "NONEXISTENTSKU", 10))
        with pytest.raises(
                exceptions.NoOrderInBatch,
                #match=f"No order line o1:COMPLICATED-LAMP in batches ['COMPLICATED-LAMP']"
        ):
            mbus.handle(commands.Deallocate("o1", "COMPLICATED-LAMP", 10))


class TestChangeBatchQuantity:
    def test_changes_available_quantity(self, fake_bus):
        """
        1. Создаем партию
        2. Меняем кол-во доступнх товар в партии

        ОР: кол-во доступных товаров в партии изменилось
        """
        mbus = fake_bus
        mbus.handle(
            commands.CreateBatch("batch1", "ADORABLE-SETTEE", 100, None)
        )
        [batch] = mbus.uow.products.get(sku="ADORABLE-SETTEE").batches
        assert batch.available_quantity == 100
        mbus.handle(commands.ChangeBatchQuantity("batch1", 50))
        assert batch.available_quantity == 50

    def test_reallocates_if_necessary(self, fake_bus):
        """
        1. Создаем две партии
        2. Пытаемся разместить два заказа, оба уходят в раннюю партию
        3. Меняем размер ранней партии так, чтобы отменился один из заказов

        ОР: один из заказов отменился и разместился в другой партии
        """
        mbus = fake_bus

        event_history = [
            commands.CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
            commands.CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            commands.Allocate("order1", "INDIFFERENT-TABLE", 20),
            commands.Allocate("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            mbus.handle(e)

        [batch1, batch2] = mbus.uow.products.get(sku="INDIFFERENT-TABLE").batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50
        mbus.handle(commands.ChangeBatchQuantity("batch1", 25))
        # размещение заказа order1 или order2 будет отменено, и у нас
        # будет 25 - 20
        assert batch1.available_quantity == 5
        # и 20 будет повторно размещено в следующей партии
        assert batch2.available_quantity == 30

    def test_reallocates_if_necessary_isolated(self, fake_bus):
        mbus = fake_bus

        # тестовые условия, как и раньше
        event_history = [
            commands.CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
            commands.CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            commands.Allocate("order1", "INDIFFERENT-TABLE", 20),
            commands.Allocate("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            mbus.handle(e)
        [batch1, batch2] = mbus.uow.products.get(sku="INDIFFERENT-TABLE").batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50
        mbus.handle(commands.ChangeBatchQuantity("batch1", 25))
        # подтвердить истинность на новых порожденных событиях,
        # а не на последующих побочных эффектах
        reallocation_command = mbus.message_published[-2]
        reallocated_event = mbus.message_published[-1]
        assert isinstance(reallocation_command, commands.Allocate)
        assert isinstance(reallocated_event, events.Allocated)
