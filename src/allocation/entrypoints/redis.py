import json
from dataclasses import asdict

from loguru import logger

import redis

from src.allocation.adapters import orm
from src.allocation.core import config
from src.allocation.models import commands, events
from src.allocation.services import messagebus, unit_of_work

r = redis.Redis(**config.get_redis_host_and_port())


def main():
    # subscribe on start
    orm.start_mappers()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe('change_batch_quantity')
    for m in pubsub.listen():
        handle_change_batch_quantity(m)


def handle_change_batch_quantity(m):
    """
    Redis Subscriber
    """
    logger.debug('handling %s', m)
    data = json.loads(m['data'])  # from redis -> event
    cmd = commands.ChangeBatchQuantity(ref=data['batchref'],
    qty=data['qty'])
    messagebus.MessageBus().handle(cmd, uow=unit_of_work.SqlAlchemyUnitOfWork())


def publish(channel, event: events.Event):
    """
    Redis publisher
    """
    # TODO can map channel topic with event's name
    logger.debug('publishing: channel=%s, event=%s', channel, event)
    r.publish(channel, json.dumps(asdict(event)))
