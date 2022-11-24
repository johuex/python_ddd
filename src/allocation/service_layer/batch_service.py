"""
Здесь будут лежать функции службы, связанные с Batch
"""
from datetime import date
from typing import Optional

from src.allocation.models import domain_models
from src.allocation.service_layer import unit_of_work


def add_batch(
    ref: str, sku: str, qty: int, eta: Optional[date],
    uow: unit_of_work.AbstractUnitOfWork
) -> None:
    with uow:
        uow.batches.add(domain_models.Batch(ref, sku, qty, eta))
        uow.commit()
