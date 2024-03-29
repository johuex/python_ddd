"""
Event receiver from Redis
"""
import json
import logging
import redis

from src.allocation.bootstrap import bus
from src.allocation.core import config
from src.allocation.models import commands

logger = logging.getLogger(__name__)

r = redis.Redis(**config.get_redis_host_and_port())


def main():
    logger.info("Redis pubsub starting")
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("change_batch_quantity")

    for m in pubsub.listen():
        handle_change_batch_quantity(m, bus)


def handle_change_batch_quantity(m, mbus):
    logger.info("handling %s", m)
    data = json.loads(m["data"])
    cmd = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    mbus.handle(cmd)


if __name__ == "__main__":
    main()
