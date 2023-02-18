from dataclasses import dataclass
from datetime import date
from typing import Optional


class Event:
    pass


@dataclass
class OutOfStock(Event):
    sku: str


@dataclass
class BatchCreated(Event):
    ref: str
    sku: str
    qty: int
    eta: Optional[date] = None


@dataclass
class AllocationRequired(Event):
    order_id: str
    sku: str
    qty: int


@dataclass
class DeAllocationRequired(Event):
    order_id: str
    sku: str
    qty: int


@dataclass
class BatchQuantityChanged(Event):
    ref: str
    qty: int


# -- Redis Events
@dataclass
class Allocated(Event):
    order_id: str
    sku: str
    qty: int
    batchref: str


@dataclass
class ToAllocate(Event):
    order_id: str
    sku: str
    qty: int


@dataclass
class Deallocated(Event):
    order_id: str
    sku: str
    qty: int
