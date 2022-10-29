from pydantic import BaseModel

from models.domain_models import OrderLine, Batch


class POSTAllocateRequest(OrderLine):
    pass


class POSTAllocateResponse(BaseModel):
    batchref: str
