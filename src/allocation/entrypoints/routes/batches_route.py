from fastapi import APIRouter, HTTPException
from fastapi.responses import ORJSONResponse

from src.allocation.bootstrap import bus
from src.allocation.models import commands
from src.allocation.models.api_models.batches_api_models import POSTBatchesResponse, POSTBatchesRequest

router = APIRouter(prefix='/batches')


@router.post("")
async def post_allocate_api(new_batch: POSTBatchesRequest):
    try:
        command = commands.CreateBatch(
            ref=new_batch.ref,
            sku=new_batch.sku,
            qty=new_batch.qty,
            eta=new_batch.eta,
        )
        bus.handle(command)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return ORJSONResponse(
        content={},
        status_code=200
    )
