"""
Здесь будут лежать функции службы, связанные с Batch
"""
from datetime import date
from typing import Optional

from adapters.repository import AbstractRepository
from models import domain_models


def add_batch(
    ref: str, sku: str, qty: int, eta: Optional[date],
    repo: AbstractRepository, session,
) -> None:
    repo.add(domain_models.Batch(ref, sku, qty, eta))
    session.commit()
