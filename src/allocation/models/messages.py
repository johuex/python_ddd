from typing import Union

from src.allocation.models import commands, events

Message = Union[commands.Command, events.Event]
