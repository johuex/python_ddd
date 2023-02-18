from typing import List, Dict

from pydantic import BaseModel


class OrderLine(BaseModel):
    orderid: str
    sku: str
    qty: int


class POSTAllocateRequest(OrderLine):
    pass


class POSTAllocateResponse(BaseModel):
    batchref: str


class DELETEAllocateRequest(OrderLine):
    pass


class DELETEAllocateResponse(BaseModel):
    batchref: str


class GetOrderAllocationsResponse(BaseModel):
    allocations: List[Dict[str, str]]


class GetAllocationResponse(BaseModel):
    allocation: Dict[str, str]
