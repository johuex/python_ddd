import json

import redis
from tenacity import Retrying, stop_after_delay

from src.allocation.core import config
from src.allocation.helpers.utils import random_orderid, random_batchref, random_sku
from tests.e2e import api_client, redis_client

r = redis.Redis(**config.get_redis_host_and_port())


def subscribe_to(channel):
    pubsub = r.pubsub()
    pubsub.subscribe(channel)
    confirmation = pubsub.get_message(timeout=3)
    assert confirmation["type"] == "subscribe"
    return pubsub


def publish_message(channel, message):
    r.publish(channel, json.dumps(message))


class TestRedisIntegration:
    def test_change_batch_quantity_leading_to_reallocation(self, postgres_db):
        """
        1. Через API создаем две партии
        2. В Redis публикуем событие по изменению кол-ва товара в партии
        3. Ждем в Redis событие Allocated о размещении товара после изменения кол-ва товара в партии

        ОР: сообщение из Redis пришло, товар разместился
        """
        # начать с двух партий и заказа, размещенного в одной из них
        orderid, sku = random_orderid(), random_sku()
        earlier_batch, later_batch = random_batchref('old'), random_batchref('newer')
        api_client.post_to_add_batch(earlier_batch, sku, qty=10, eta='2011-01-02')
        api_client.post_to_add_batch(later_batch, sku, qty=10, eta='2011-01-02')
        response = api_client.post_to_allocate(orderid, sku, 10)
        assert response.json()['batchref'] == earlier_batch
        subscription = redis_client.subscribe_to('line_allocated')
        # изменить количество товара в размещенной партии,
        # чтобы оно было меньше, чем в заказе
        redis_client.publish_message('change_batch_quantity', {
            'batchref': earlier_batch, 'qty': 5
            }
        )
        # подождать до тех пор, пока мы не увидим сообщение
        # о повторном размещении заказа
        messages = []
        for attempt in Retrying(stop=stop_after_delay(3), reraise=True):
            with attempt:
                message = subscription.get_message(timeout=1)
                if message:
                    messages.append(message)
                    print(messages)
                data = json.loads(messages[-1]['data'])
                assert data['order_id'] == orderid
                assert data['batchref'] == later_batch
