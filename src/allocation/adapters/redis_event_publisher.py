"""
Event publisher to Redis
"""
import json
import logging
from dataclasses import asdict
import redis

from src.allocation.core import config
from src.allocation.models import events

logger = logging.getLogger(__name__)

r = redis.Redis(**config.get_redis_host_and_port())


def publish(channel, event: events.Event):
    logging.info("publishing: channel=%s, event=%s", channel, event)
    r.publish(channel, json.dumps(asdict(event)))
