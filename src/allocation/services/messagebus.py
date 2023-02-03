from src.allocation.adapters import email
from src.allocation.models import events


def handle(event: events.Event):
    for handler in HANDLERS[type(event)]:
        handler(event)


def send_out_of_stock_notification(event: events.OutOfStock):
    email.send_email('stock@made.com', f'Артикула {event.sku} нет в наличии',)


HANDLERS = {
    events.OutOfStock: [send_out_of_stock_notification],
}  # тип: Dict[Type[events.Event], List[Callable]]
