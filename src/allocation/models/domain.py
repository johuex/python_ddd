from dataclasses import dataclass
from datetime import date
from typing import Optional, List

from src.allocation.models import commands, events
from src.allocation.models.exceptions import NoOrderInBatch, OutOfStock


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

    def __repr__(self):
        return f"<Batch {self.reference}>"

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

    def can_deallocate(self, line: OrderLine):
        return line in self._allocations

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if self.can_deallocate(line):
            self._allocations.remove(line)

    def deallocate_random_one(self) -> OrderLine:
        return self._allocations.pop()


class Product:
    """
    Агрегат, все партии с определенным артикулом
    """
    def __init__(self, sku: str, batches: List[Batch], version: int = 0):
        self.sku = sku  # идентифицирует каждый "продукт"
        self.batches = batches  # все партии этого артикула
        self.version = version  # UUID can be there instead of counter
        self.events = []  # тип: List[events.Event]

    def allocate(self, line: OrderLine) -> str:
        """
        Автономная функция для службы предметной области;
        Служба предметной области
        Размещение товара в одной из партий
        """
        try:
            batch = next(
                b for b in sorted(self.batches) if b.can_allocate(line)
            )
            batch.allocate(line)
            self.version += 1
            self.events.append(events.Allocated(
                order_id=line.orderid, sku=line.sku, qty=line.qty, batchref=batch.reference
            ))
            return batch.reference
        except StopIteration:
            raise OutOfStock(f"Out of stock for sku {line.sku}")

    def deallocate(self, line: OrderLine) -> str:
        try:
            batch = next(
                b for b in sorted(self.batches) if b.can_deallocate(line)
            )
            batch.deallocate(line)
            self.version -= 1
            return batch.reference
        except StopIteration:
            raise NoOrderInBatch(line.orderid, line.sku, [b.sku for b in self.batches])

    def change_batch_quantity(self, ref: str, qty: int):
        batch = next(b for b in self.batches if b.reference == ref)
        batch._purchased_quantity = qty
        while batch.available_quantity < 0:
            line = batch.deallocate_random_one()
            # trying to allocate deallocated order in new batch
            self.events.append(events.Deallocated(line.orderid, line.sku, line.qty))
