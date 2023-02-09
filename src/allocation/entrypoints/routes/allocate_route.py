from fastapi import APIRouter, HTTPException

from src.allocation.models import events
from src.allocation.models.api_models.assertion_api_models import (
    POSTAllocateResponse,
    POSTAllocateRequest,
    DELETEAllocateResponse,
    DELETEAllocateRequest
)
from src.allocation.services import unit_of_work, messagebus
from src.allocation.models.exceptions import InvalidSku

router = APIRouter(prefix='/allocate')


@router.post("/", response_model=POSTAllocateResponse)
async def post_allocate_api(order_line: POSTAllocateRequest):
    try:
        # create event
        event = events.AllocationRequired(
            order_id=order_line.orderid,
            sku=order_line.sku,
            qty=order_line.qty,
        )
        # send it to messagebus and wait for result
        result = messagebus.MessageBus().handle(event, unit_of_work.SqlAlchemyUnitOfWork())
    except InvalidSku as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {'batchref': result.pop(0)}


@router.delete("/", response_model=DELETEAllocateResponse)
async def delete_allocate_api(order_line: DELETEAllocateRequest):
    try:
        event = events.DeAllocationRequired(
            order_id=order_line.orderid,
            sku=order_line.sku,
            qty=order_line.qty,
        )
        result = messagebus.MessageBus().handle(event, unit_of_work.SqlAlchemyUnitOfWork())
    except InvalidSku as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {'batchref': result.pop(0)}
