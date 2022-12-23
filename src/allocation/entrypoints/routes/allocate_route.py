from fastapi import APIRouter, HTTPException

from src.allocation.models.api_models.assertion_api_models import (
    POSTAllocateResponse,
    POSTAllocateRequest,
    DELETEAllocateResponse,
    DELETEAllocateRequest
)
from src.allocation.service_layer import allocate_service, unit_of_work
from src.allocation.models.exceptions import InvalidSku

router = APIRouter(prefix='/allocate')


@router.post("/", response_model=POSTAllocateResponse)
async def post_allocate_api(order_line: POSTAllocateRequest):
    try:
        batchref = allocate_service.allocate(
            order_line.orderid,
            order_line.sku,
            order_line.qty,
            unit_of_work.SqlAlchemyUnitOfWork()
        )  # передаем полномочия на службу
    except InvalidSku as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {'batchref': batchref}


@router.delete("/", response_model=DELETEAllocateResponse)
async def delete_allocate_api(order_line: DELETEAllocateRequest):
    try:
        batchref = allocate_service.deallocate(
            order_line.orderid,
            order_line.sku,
            order_line.qty,
            unit_of_work.SqlAlchemyUnitOfWork()
        )  # передаем полномочия на службу
    except InvalidSku as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {'batchref': batchref}
