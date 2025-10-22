from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict

from conductor.shared.event.configuration.queue_worker import QueueWorkerConfiguration


class QueueConfiguration(ABC):
    WORKER_CONSUMER_KEY: ClassVar[str] = "consumer"
    WORKER_PRODUCER_KEY: ClassVar[str] = "producer"

    def __init__(self, queue_name: str, queue_type: str):
        self.queue_name = queue_name
        self.queue_type = queue_type
        self.worker_configuration = {}

    def add_consumer(self, worker_configuration: QueueWorkerConfiguration) -> None:
        self.worker_configuration[self.WORKER_CONSUMER_KEY] = worker_configuration

    def add_producer(self, worker_configuration: QueueWorkerConfiguration) -> None:
        self.worker_configuration[self.WORKER_PRODUCER_KEY] = worker_configuration

    @abstractmethod
    def get_worker_configuration(self) -> Dict[str, Any]:
        raise NotImplementedError
