"""
Здесь будут лежать функции службы, связанные с Batch
"""
from datetime import date
from typing import Optional

from src.allocation.models import domain
from src.allocation.services import unit_of_work


def add_batch(
    ref: str, sku: str, qty: int, eta: Optional[date],
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get(sku=sku)
        if product is None:
            product = domain.Product(sku, batches=[])
            uow.products.add(product)
        product.batches.append(domain.Batch(ref, sku, qty, eta))
        uow.commit()
