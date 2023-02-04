from fastapi import APIRouter, HTTPException, Response

from src.allocation.models import events
from src.allocation.models.api_models.batches_api_models import POSTBatchesResponse, POSTBatchesRequest
from src.allocation.services import unit_of_work, messagebus

router = APIRouter(prefix='/batches')


@router.post("/")
async def post_allocate_api(new_batch: POSTBatchesRequest):
    try:
        event = events.BatchCreated(
            ref=new_batch.ref,
            sku=new_batch.sku,
            qty=new_batch.qty,
            eta=new_batch.eta,
        )
        messagebus.handle(event, unit_of_work.SqlAlchemyUnitOfWork())
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return {}
