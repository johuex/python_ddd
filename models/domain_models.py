from dataclasses import dataclass
from datetime import date
from typing import Optional, List


@dataclass(unsafe_hash=True)
# frozen == immutable, немутируемый, то есть не можем менять значение после инициализации,
# unsafe_hash - добавляем неявный метод __hash__
# Наличие __hash__() означает, что сущности класса неизменны.
class OrderLine:
    """
    Модель товарной позиции (то, что заказывают)
    """
    orderid: str  # id товарной позиции
    sku: str  # stock-keeping unitб артикул
    qty: int  # quantity кол-во


class Batch:
    """
    Модель партии товара (то, что можно купить)
    """
    def __init__(
        self, ref: str, sku: str, qty: int, eta: Optional[date]
    ):
        self.reference = ref
        self.sku = sku # stock-keeping unit, артикул
        self.eta = eta  # estimated-time-arrived, ожидаемое время прибытия
        self._allocations = set()  # храним OrderLine
        self._purchased_quantity = qty

    def __eq__(self, other):
        """
        Эквивалентность, поведение класса для оператора ==
        """
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __gt__(self, other):
        """
        Сравнение, поведение класса для оператора >
        """
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def __hash__(self):
        """
        Управления поведением объектов, когда вы
        добавляете их в коллекции или используете в качестве ключей словаря
        dict, тк объекты должны быть уникальны
        """
        return hash(self.reference)

    @property  # вычисляемое свойство
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)
    
    @property
    def available_quantity(self) -> int:  # доступно для заказа
        return self._purchased_quantity - self.allocated_quantity   
    
    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)


class OutOfStock(Exception):
    pass


def allocate(line: OrderLine, batches: List[Batch]) -> str:
    """
    Автономная функция для службы предметной области;
    Служба предметной области
    """
    try:
        batch = next(
            b for b in sorted(batches) if b.can_allocate(line)
        )
        batch.allocate(line)
        return batch.reference
    except StopIteration:
        raise OutOfStock(f"Out of stock for sku {line.sku}")
