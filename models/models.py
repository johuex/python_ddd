from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
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
        self.sku = sku # stock-keeping unitб артикул
        self.eta = eta  # estimated-time-arrived, ожидаемое время прибытия
        self._allocations = set()  # храним OrderLine
        self._purchased_quantity = qty  #

    @property # вычисляемое свойство
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
