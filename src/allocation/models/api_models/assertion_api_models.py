from pydantic import BaseModel

from src.allocation.models.domain_models import OrderLine


class POSTAllocateRequest(OrderLine):
    pass


class POSTAllocateResponse(BaseModel):
    batchref: str


class DELETEAllocateRequest(OrderLine):
    pass


class DELETEAllocateResponse(BaseModel):
    batchref: str
