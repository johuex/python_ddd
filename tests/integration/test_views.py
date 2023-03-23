from datetime import date

from src.allocation.models import commands
from src.allocation.services import views


today = date.today()


class TestViews:
    def test_allocations_view(self, real_bus):
        mbus = real_bus

        mbus.handle(commands.CreateBatch('sku1batch', 'sku1', 50, None))
        mbus.handle(commands.CreateBatch('sku2batch', 'sku2', 50, today))
        mbus.handle(commands.Allocate('order1', 'sku1', 20))
        mbus.handle(commands.Allocate('order1', 'sku2', 20))
        # добавим фальшивую партию и заказ,
        # чтобы убедиться, что мы получаем правильные значения
        mbus.handle(commands.Allocate('otherorder', 'sku1', 30))
        mbus.handle(commands.CreateBatch('sku1batch-later', 'sku1', 50, today))
        mbus.handle(commands.Allocate('otherorder', 'sku2', 10))

        assert views.allocations(mbus.uow, 'order1') == [
            {'sku': 'sku1', 'batchref': 'sku1batch'},
            {'sku': 'sku2', 'batchref': 'sku2batch'},
        ]

    def test_deallocation_view(self, real_bus):
        mbus = real_bus

        mbus.handle(commands.CreateBatch("br1", "sku13", 50, None))
        mbus.handle(commands.CreateBatch("br2", "sku13", 50, today))
        mbus.handle(commands.Allocate("or1", "sku13", 40))
        mbus.handle(commands.ChangeBatchQuantity("br1", 10))

        assert views.allocations(mbus.uow, "or1") == [
            {"sku": "sku13", "batchref": "br2"},
        ]
