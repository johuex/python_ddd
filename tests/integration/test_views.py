from datetime import date

from src.allocation.models import commands
from src.allocation.services import unit_of_work, messagebus, views


today = date.today()


class TestViews:
    def test_allocations_view(self, postgres_session):
        uow = unit_of_work.SqlAlchemyUnitOfWork(postgres_session)
        mbus = messagebus.MessageBus()

        mbus.handle(commands.CreateBatch('sku1batch', 'sku1', 50, None), uow)
        mbus.handle(commands.CreateBatch('sku2batch', 'sku2', 50, today), uow)
        mbus.handle(commands.Allocate('order1', 'sku1', 20), uow)
        mbus.handle(commands.Allocate('order1', 'sku2', 20), uow)
        # добавим фальшивую партию и заказ,
        # чтобы убедиться, что мы получаем правильные значения
        mbus.handle(commands.Allocate('otherorder', 'sku1', 30), uow)
        mbus.handle(commands.CreateBatch('sku1batch-later', 'sku1', 50, today), uow)
        mbus.handle(commands.Allocate('otherorder', 'sku2', 10), uow)

        assert views.allocations(uow, 'order1') == [
            {'sku': 'sku1', 'batchref': 'sku1batch'},
            {'sku': 'sku2', 'batchref': 'sku2batch'},
        ]

    def test_deallocation_view(self, postgres_session):
        uow = unit_of_work.SqlAlchemyUnitOfWork(postgres_session)
        mbus = messagebus.MessageBus()

        mbus.handle(commands.CreateBatch("br1", "sku13", 50, None), uow)
        mbus.handle(commands.CreateBatch("br2", "sku13", 50, today), uow)
        mbus.handle(commands.Allocate("or1", "sku13", 40), uow)
        mbus.handle(commands.ChangeBatchQuantity("br1", 10), uow)

        assert views.allocations(uow, "or1") == [
            {"sku": "sku13", "batchref": "br2"},
        ]
