from datetime import date
from src.allocation.models.domain_models import Batch, OrderLine


def make_batch_and_line(sku, batch_qty, line_qty):
    return (
    Batch("batch-001", sku, batch_qty, eta=date.today()),
    OrderLine("order-123", sku, line_qty)
    )


class TestAllocateBatches:
    def test_allocating_to_a_batch_reduces_the_available_quantity(self):
        """
        1. Создаем партию на 20 штук
        2. Создаем товарную позицию на 2 шт
        3. Выделяем товарную позицию в партии
        ОР: в партии осталось 18 штук
        """
        batch = Batch("batch-001", "SMALL-TABLE", qty=20, eta=date.today())
        line = OrderLine('order-ref', "SMALL-TABLE", 2)
        batch.allocate(line)
        assert batch.available_quantity == 18

    def test_can_allocate_if_available_greater_than_required(self):
        """
        1. Создаем партию на 20 штук
        2. Создаем товарную позицию на 2 шт
        3. Проверяем возможность сохранения товарной позиции в партии
        ОР: ОК
        """
        large_batch, small_line = make_batch_and_line("ELEGANT-LAMP", 20, 2)
        assert large_batch.can_allocate(small_line)

    def test_cannot_allocate_if_available_smaller_than_required(self):
        """
        1. Создаем партию на 2 штук
        2. Создаем товарную позицию на 20 шт
        3. Проверяем возможность сохранения товарной позиции в партии
        ОР: False (не хватает доступных товаров)
        """
        small_batch, large_line = make_batch_and_line("ELEGANT-LAMP", 2, 20)
        assert not small_batch.can_allocate(large_line)

    def test_can_allocate_if_available_equal_to_required(self):
        """
        1. Создаем партию на 2 штук
        2. Создаем товарную позицию на 2 шт
        3. Проверяем возможность сохранения товарной позиции в партии
        ОР: ОК
        """
        batch, line = make_batch_and_line("ELEGANT-LAMP", 2, 2)
        assert batch.can_allocate(line)

    def test_cannot_allocate_if_skus_do_not_match(self):
        """
        1. Создаем партию на 100 штук с артикулем UNCOMFORTABLE-CHAIR
        2. Создаем товарную позицию на 10 шт с артикулем EXPENSIVE-TOASTER
        3. Проверяем возможность сохранения товарной позиции в партии
        ОР: False (разные артикули)
        """
        batch = Batch("batch-001", "UNCOMFORTABLE-CHAIR", 100, eta=None)
        different_sku_line = OrderLine("order-123", "EXPENSIVE-TOASTER", 10)
        assert not batch.can_allocate(different_sku_line)

    def test_can_only_deallocate_allocated_lines(self):
        """
        1. Создаем партию на 20 штук
        2. Создаем товарную позицию на 2 шт
        3. Отменяем товарной позиции в партии
        4. Проверяем кол-во товара в партии
        ОР: ОК (кол-во товара не изменится)
        """
        batch, unallocated_line = make_batch_and_line("DECORATIVE-TRINKET", 20, 2)
        batch.deallocate(unallocated_line)
        assert batch.available_quantity == 20

    def test_allocation_is_idempotent(self):
        """
        1. Создаем партию на 20 штук
        2. Создаем товарную позицию на 2 шт
        3. Сохраняем товарной позиции в партии первый раз
        4. Сохраняем товарной позиции в партии второй раз
        5. Проверяем кол-во товара в партии
        ОР: ОК (кол-во товара не изменится после первой товарной позиции)
        """
        batch, line = make_batch_and_line("ANGULAR-DESK", 20, 2)
        batch.allocate(line)
        batch.allocate(line)
        assert batch.available_quantity == 18


class TestDeallocateBatches:

    def test_deallocation_exist_line_in_batch_return_true(self):
        """
        1. Создадим партию
        2. Создаем товарную позицию
        3. Размещаем товарную позицию в партии
        4. Отменяем товарную позицию в партии
        ОР: Кол-во доступных товаров в партии вернулось в изначальное значение
        """
        batch, line = make_batch_and_line("ANGULAR-DESK", 20, 2)
        batch.allocate(line)
        assert batch.available_quantity == 18
        batch.deallocate(line)
        assert batch.available_quantity == 20

    def test_deallocate_non_exist_line_in_batch_return_false(self):
        """
        1. Создадим партию
        2. Создаем товарную позицию
        3. Пытаемся отменить неразмещенную товарную позицию в партии
        ОР: кол-во товара в партии не изменится
        """
        batch, line = make_batch_and_line("ANGULAR-DESK", 20, 2)
        assert batch.available_quantity == 20
        batch.deallocate(line)
        assert batch.available_quantity == 20
