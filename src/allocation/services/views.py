from src.allocation.services import unit_of_work


def allocations(uow: unit_of_work.SqlAlchemyUnitOfWork, order_id: str):
    with uow:
        results = uow.session.execute(
            """
            SELECT sku, batchref FROM allocations_view WHERE order_id = :orderid
            """,
            dict(orderid=order_id),
        )
    return [dict(r) for r in results]


def allocation(uow: unit_of_work.SqlAlchemyUnitOfWork, order_id: str, sku: str):
    with uow:
        result = uow.session.execute(
            """
            SELECT sku, batchref FROM allocations_view WHERE order_id = :orderid and sku = :sku
            """,
            dict(orderid=order_id, sku=sku),
        )
    return dict(result)
