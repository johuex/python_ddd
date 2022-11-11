from fastapi import APIRouter, HTTPException

from entrypoints.main import get_session
from models.api_models.assertion_api_models import (
    POSTAllocateResponse,
    POSTAllocateRequest,
    DELETEAllocateResponse,
    DELETEAllocateRequest
)
from service_layer import allocate_service
from adapters import repository
from models import domain_models


router = APIRouter(prefix='/allocate')


@router.post("/", response_model=POSTAllocateResponse)
async def post_allocate_api(order_line: POSTAllocateRequest):
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)  # создаем несколько объектов репозитория
    try:
        batchref = allocate_service.allocate(
            order_line.orderid,
            order_line.sku,
            order_line.qty,
            repo,
            session
        )  # передаем полномочия на службу
    except domain_models.OutOfStock as e:
        return HTTPException(status_code=400, detail=str(e))

    session.commit()

    return {'batchref': batchref}


@router.delete("/", response_model=DELETEAllocateResponse)
async def delete_allocate_api(order_line: DELETEAllocateRequest):
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)  # создаем несколько объектов репозитория
    try:
        batchref = allocate_service.deallocate(
            order_line.orderid,
            order_line.sku,
            order_line.qty,
            repo,
            session
        )  # передаем полномочия на службу
    except domain_models.NoOrderInBatch as e:
        return HTTPException(status_code=400, detail=str(e))

    session.commit()

    return {'batchref': batchref}
