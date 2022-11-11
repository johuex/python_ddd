from fastapi import APIRouter

from adapters import repository
from entrypoints.main import get_session
from models.api_models.batches_api_models import POSTBatchesResponse, POSTBatchesRequest
from service_layer import batch_service

router = APIRouter(prefix='/batches')


@router.post("/", response_model=POSTBatchesResponse)
async def post_allocate_api(new_batch: POSTBatchesRequest):
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)  # создаем несколько объектов репозитория
    batch_service.add_batch(
        new_batch.ref,
        new_batch.sku,
        new_batch.qty,
        new_batch.eta,
        repo,
        session
    )  # передаем полномочия на службу

    session.commit()

    return new_batch
