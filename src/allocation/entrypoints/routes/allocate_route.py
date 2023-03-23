from fastapi import APIRouter, HTTPException
from fastapi.responses import ORJSONResponse

from src.allocation.bootstrap import bus
from src.allocation.models import commands
from src.allocation.models.api_models.assertion_api_models import (
    POSTAllocateResponse,
    POSTAllocateRequest,
    DELETEAllocateResponse,
    DELETEAllocateRequest, GetOrderAllocationsResponse, GetAllocationResponse
)
from src.allocation.services import views
from src.allocation.models.exceptions import InvalidSku

router = APIRouter(prefix='/allocate')


@router.get("/{order_id}", response_model=GetOrderAllocationsResponse)
async def get_order_allocations(order_id: str):
    try:
        uow = bus.uow
        result = views.allocations(uow, order_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    if not result:
        return ORJSONResponse(
            content={"error": "Not Found"},
            status_code=404
        )
    return ORJSONResponse(
        content={
            "allocations": result
        },
        status_code=200
    )


@router.get("/{order_id}/{sku}", response_model=GetAllocationResponse)
async def get_allocation(order_id: str, sku: str):
    try:
        uow = bus.uow
        result = views.allocation(uow, order_id, sku)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    if not result:
        return ORJSONResponse(
            content={"error": "Not Found"},
            status_code=404
        )
    return ORJSONResponse(
        content={
            "allocations": result
        },
        status_code=200
    )


@router.post("", response_model=POSTAllocateResponse)
async def post_allocate_api(order_line: POSTAllocateRequest):
    try:
        # create event
        command = commands.Allocate(
            order_id=order_line.orderid,
            sku=order_line.sku,
            qty=order_line.qty,
        )
        # send it to messagebus and wait for result
        result = bus.handle(command)
    except InvalidSku as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {'batchref': result.pop(0)}


@router.delete("", response_model=DELETEAllocateResponse)
async def delete_allocate_api(order_line: DELETEAllocateRequest):
    try:
        command = commands.Deallocate(
            order_id=order_line.orderid,
            sku=order_line.sku,
            qty=order_line.qty,
        )
        result = bus.handle(command)
    except InvalidSku as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {'batchref': result.pop(0)}
