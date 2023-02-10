from typing import Any

import requests

from src.allocation.core import config


def post_to_add_batch(ref: str, sku: str, qty: int, eta: Any):
    url = config.get_api_url()
    r = requests.post(
        f"{url}/batches", json={"ref": ref, "sku": sku, "qty": qty, "eta": eta}
    )
    assert r.status_code == 200


def post_to_allocate(orderid, sku, qty, expect_success=True):
    url = config.get_api_url()
    r = requests.post(
        f"{url}/allocate",
        json={
            "orderid": orderid,
            "sku": sku,
            "qty": qty,
        },
    )
    if expect_success:
        assert r.status_code == 200
    return r
