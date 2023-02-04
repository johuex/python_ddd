"""
E2E (сквозные) тесты для API
"""
from typing import Any

import requests

from src.allocation.core import config
from src.allocation.helpers.utils import random_sku, random_batchref, random_orderid


_baseurl = f"{config.get_api_url()}/allocate"


def post_to_add_batch(ref: str, sku: str, qty: int, eta: Any):
    url = config.get_api_url()
    r = requests.post(
        f"{url}/batches", json={"ref": ref, "sku": sku, "qty": qty, "eta": eta}
    )
    assert r.status_code == 200


class TestApiPostAllocation:
    """allocate line to batch by entrypoints tests"""
    def test_happy_path_returns_200_and_allocated_batch(self, postgres_db):
        """
        1. Создаем три партии + записываем их в БД
        2. Через API размещаем позицию на 3 шт
        ОР: позиция разместится в ранней партии
        """
        sku, othersku = random_sku(), random_sku("other")
        earlybatch = random_batchref(1)
        laterbatch = random_batchref(2)
        otherbatch = random_batchref(3)
        post_to_add_batch(laterbatch, sku, 100, "2011-01-02")
        post_to_add_batch(earlybatch, sku, 100, "2011-01-01")
        post_to_add_batch(otherbatch, othersku, 100, None)
        data = {
            "orderid": random_orderid(), "sku": sku, "qty": 3
        }

        res = requests.post(_baseurl, json=data)

        assert res.status_code == 200
        assert res.json()["batchref"] == earlybatch

    def test_unhappy_path_returns_400_and_error_message(self, postgres_db):
        """
        1. Создаем товарную позицию
        2. Пробуем разместить ее в несуществующей партии (тк она не создана)
        ОР: позиция не размещена, Invalid sku
        """
        unknown_sku, orderid = random_sku(), random_orderid()
        data = {"orderid": orderid, "sku": unknown_sku, "qty": 20}

        res = requests.post(_baseurl, json=data)

        assert res.status_code == 400
        assert res.json()["detail"] == f"Invalid stock-keeping: {unknown_sku}"


class TestApiDeleteAllocation:
    """deallocate line to batch by entrypoints tests"""

    def test_happy_path_returns_200_and_deallocated_batch(self, postgres_db):
        """
        1. Создаем три партии + записываем их в БД
        2. Через API размещаем позицию на 3 шт
        3. Через API отменяем размещение позиии
        ОР: позиция отменится верно (в самой ранней партии)
        """
        sku, othersku = random_sku(), random_sku("other")
        earlybatch = random_batchref(1)
        laterbatch = random_batchref(2)
        otherbatch = random_batchref(3)
        post_to_add_batch(laterbatch, sku, 100, "2011-01-02")
        post_to_add_batch(earlybatch, sku, 100, "2011-01-01")
        post_to_add_batch(otherbatch, othersku, 100, None)
        data = {
            "orderid": random_orderid(), "sku": sku, "qty": 3
        }

        res = requests.post(_baseurl, json=data)

        assert res.status_code == 200
        assert res.json()["batchref"] == earlybatch

        res_2 = requests.delete(_baseurl, json=data)

        assert res_2.status_code == 200
        assert res_2.json()["batchref"] == earlybatch
        # TODO тут бы еще проверять кол-во в партии, что оно верно

    def test_deallocate_order_in_clean_batch_return_false(self, postgres_db):
        """
        1. Создаем партию
        2. Создаем товарную позицию
        3. Пробуем отменить неразмещенную позицию в партии
        ОР: позиция не отменена,
        """
        batch_sku = random_sku()
        earlybatch = random_batchref(1)
        post_to_add_batch(earlybatch, batch_sku, 100, "2011-01-01")

        unknown_sku, orderid = random_sku(), random_orderid()
        data = {"orderid": orderid, "sku": unknown_sku, "qty": 20}

        res = requests.post(_baseurl, json=data)

        assert res.status_code == 400
        assert res.json()["detail"] == f"Invalid stock-keeping: {unknown_sku}"
