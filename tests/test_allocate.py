from datetime import date, timedelta

import pytest

from models.domain_models import allocate, OrderLine, Batch, OutOfStock, deallocate
from models.exceptions import NoOrderInBatch

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


class TestAllocate:

    def test_prefers_current_stock_batches_to_shipments(self):
        """
        1. Создаем партию на 100 шт 'на складе'
        2. Создаем аналогичную по артикулу партию на 100 шт 'в пути', время прибытия - завтра
        3. Создаем товарную позицию на 10 шт
        4. Пробуем разместить ее в одной из партий
        ОР: Товарная позиция разместилась в ранней по eta партии
        """
        in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
        shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
        line = OrderLine("oref", "RETRO-CLOCK", 10)

        allocate(line, [in_stock_batch, shipment_batch])

        assert in_stock_batch.available_quantity == 90
        assert shipment_batch.available_quantity == 100

    def test_prefers_earlier_batches(self):
        """
        1. Создаем партию на 100 шт с eta - сегодня
        2. Создаем партию на 100 шт с eta - завтра
        3. Создаем партию на 100 шт с eta - позже
        4. Создаем товарную позицию на 10 шт
        5. Пробуем разместить ее в одной из партий
        ОР: Товарная позиция разместилась в ранней по eta партии
        """
        earliest = Batch("speedy-batch", "MINIMALIST-SPOON", 100, eta=today)
        medium = Batch("normal-batch", "MINIMALIST-SPOON", 100, eta=tomorrow)
        latest = Batch("slow-batch", "MINIMALIST-SPOON", 100, eta=later)
        line = OrderLine("order1", "MINIMALIST-SPOON", 10)

        allocate(line, [medium, earliest, latest])

        assert earliest.available_quantity == 90
        assert medium.available_quantity == 100
        assert latest.available_quantity == 100

    def test_returns_allocated_batch_ref(self):
        """
        1. Создаем партию на 100 шт с eta - прям сейчас
        2. Создаем партию на 100 шт с eta - завтра
        3. Создаем товарную позицию на 10 шт
        4. Пробуем разместить ее в одной из партий
        5. Проверяем, что товарная позиция разместилась в партии с ранней eta через .reference
        ОР: OK
        """
        in_stock_batch = Batch("in-stock-batch-ref", "HIGHBROW-POSTER", 100, eta=None)
        shipment_batch = Batch("shipment-batch-ref", "HIGHBROW-POSTER", 100, eta=tomorrow)
        line = OrderLine("oref", "HIGHBROW-POSTER", 10)

        allocation = allocate(line, [in_stock_batch, shipment_batch])

        assert allocation == in_stock_batch.reference

    def test_raises_out_of_stock_exception_if_cannot_allocate(self):
        """
        1. Создаем партию на 10 шт
        2. Создаем товарную позицию на 10 шт и размещаем ее в партии
        3. Пытаемся разместить товарную позицию на 1 шт в ту же партию
        ОР: OutOfStock - товаров нет в наличии
        """
        batch = Batch('batch1', 'SMALL-FORK', 10, eta=today)
        allocate(OrderLine('order1', 'SMALL-FORK', 10), [batch])
        with pytest.raises(OutOfStock, match='Out of stock for sku SMALL-FOR'):  # на что влияет match?
            allocate(OrderLine('order2', 'SMALL-FORK', 1), [batch])


class TestDeallocate:

    def test_deallocate_line_in_one_batch_return_ok(self):
        """
        1. Создаем партию товара
        2. Создаем товарную позицию
        3. Размещаем товарную позицию в партии
        4. Отменяем размещение
        ОК: размещение отменилось в партии
        """
        in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
        line = OrderLine("oref", "RETRO-CLOCK", 10)

        allocate(line, [in_stock_batch])
        assert in_stock_batch.available_quantity == 90

        deallocate(line, [in_stock_batch])
        assert in_stock_batch.available_quantity == 100

    def test_deallocate_line_in_one_of_batches_return_ok(self):
        """
        1. Создаем несколько партий товара
        2. Создаем товарную позицию
        3. Размещаем товарную позицию в партии
        4. Отменяем размещение
        ОК: размещение отменилось в верной партии (самой ранней)
        """
        in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
        shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
        line = OrderLine("oref", "RETRO-CLOCK", 10)

        allocate(line, [in_stock_batch, shipment_batch])

        assert in_stock_batch.available_quantity == 90
        assert shipment_batch.available_quantity == 100

        deallocate(line, [in_stock_batch, shipment_batch])

        assert in_stock_batch.available_quantity == 100
        assert shipment_batch.available_quantity == 100

    def test_deallocate_line_in_no_one_of_batches_return_error(self):
        """
        1. Создаем несколько партий товара
        2. Создаем товарную позицию
        4. Отменяем размещение, которое нигде не размещали
        ОК: NoOrderInBatch
        """
        in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
        shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
        line = OrderLine("oref", "RETRO-CLOCK", 10)

        assert in_stock_batch.available_quantity == 100
        assert shipment_batch.available_quantity == 100
        with pytest.raises(NoOrderInBatch):
            deallocate(line, [in_stock_batch, shipment_batch])

        assert in_stock_batch.available_quantity == 100
        assert shipment_batch.available_quantity == 100
