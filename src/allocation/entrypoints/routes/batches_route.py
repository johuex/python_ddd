from fastapi import APIRouter

from src.allocation.models.api_models.batches_api_models import POSTBatchesResponse, POSTBatchesRequest
from src.allocation.services import batch_service, unit_of_work

router = APIRouter(prefix='/batches')


@router.post("/", response_model=POSTBatchesResponse)
async def post_allocate_api(new_batch: POSTBatchesRequest):
    batch_service.add_batch(
        new_batch.ref,
        new_batch.sku,
        new_batch.qty,
        new_batch.eta,
        unit_of_work.SqlAlchemyUnitOfWork()
    )  # передаем полномочия на службу

    return new_batch
