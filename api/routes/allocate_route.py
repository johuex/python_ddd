from fastapi import APIRouter, HTTPException

import repository
from api.main import get_session
from models.api_models.assertion_api_models import POSTAllocateResponse, POSTAllocateRequest
from services import allocate_service
from models import domain_models


router = APIRouter(prefix='/allocate')


@router.post("/", response_model=POSTAllocateResponse)
async def allocate_api(order_line: POSTAllocateRequest):
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)  # создаем несколько объектов репозитория
    line = domain_models.OrderLine(
        order_line.orderid,
        order_line.sku,
        order_line.qty,
    )

    try:
        batchref = allocate_service.allocate(line, repo, session)  # передаем полномочия на службу
    except domain_models.OutOfStock as e:
        return HTTPException(status_code=400, detail=str(e))

    session.commit()

    return {'batchref': batchref}
