from abc import ABC, abstractmethod
from typing import Optional
from logger import prepare_logger


class Link(ABC):
    """
    Abstract class to handle communications between Raspberry Pi and other components
    - send(message: str)
    - recv()
    """

    def __init__(self):
        """
        Constructor for Link.
        """
        self.logger = prepare_logger()

    @abstractmethod
    def send(self, message: str) -> None:
        pass

    @abstractmethod
    def recv(self) -> Optional[str]:
        pass
