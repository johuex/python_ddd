import abc


class AbstractNotification(abc.ABC):
    @abc.abstractmethod
    def send(self, *args, **kwargs):
        raise NotImplementedError


class EmailNotification(AbstractNotification):
    def send(self, recipient: str, message: str):
        print(f"Email send to {recipient}, message: {message}")
