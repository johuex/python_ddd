from sqlalchemy import Table, Column, Integer, String, Date, ForeignKey, event
from sqlalchemy.orm import registry, relationship

from src.allocation.models import domain

mapper_registry = registry()
metadata = mapper_registry.metadata
metadata.schema = "public"

order_lines = Table(
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sku", String(255)),
    Column("qty", Integer, nullable=False),
    Column("orderid", String(255)),
)

products = Table(
    "products",
    metadata,
    Column("sku", String(255), primary_key=True),
    Column("version", Integer, nullable=False, server_default="0"),
)


batches = Table(
    "batches",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255)),
    Column("sku", String(255), ForeignKey("products.sku")),
    Column("_purchased_quantity", Integer, nullable=False),
    Column("eta", Date, nullable=True),
)

allocations = Table(
    "allocations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("orderline_id", ForeignKey("order_lines.id")),
    Column("batch_id", ForeignKey("batches.id")),
)


def start_mappers():
    """
    Классическое попарное отображение предметной модели на orm модель
    """
    lines_mapper = mapper_registry.map_imperatively(domain.OrderLine, order_lines)
    batches_mapper = mapper_registry.map_imperatively(
        domain.Batch,
        batches,
        properties={
            "_allocations": relationship(
                lines_mapper, secondary=allocations, collection_class=set,
            )
        },
    )
    mapper_registry.map_imperatively(domain.Product, products, properties={"batches": relationship(batches_mapper)})


@event.listens_for(domain.Product, "load")
def receive_load(product, _):
    product.events = []

