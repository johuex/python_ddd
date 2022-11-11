from typing import Any

from pydantic import BaseModel


class POSTBatchesRequest(BaseModel):
    ref: str
    sku: str
    qty: int
    eta: Any


class POSTBatchesResponse(POSTBatchesRequest):
    pass
