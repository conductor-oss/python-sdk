from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.api.event_resource_api import (
    EventResourceApiAdapter,
)
from conductor.shared.event.configuration import QueueConfiguration


class AsyncEventClient:
    def __init__(self, api_client: ApiClient):
        self.client = EventResourceApiAdapter(api_client)

    async def delete_queue_configuration(self, queue_configuration: QueueConfiguration) -> None:
        return await self.client.delete_queue_config(
            queue_name=queue_configuration.queue_name,
            queue_type=queue_configuration.queue_type,
        )

    async def get_kafka_queue_configuration(self, queue_topic: str) -> QueueConfiguration:
        return await self.get_queue_configuration(
            queue_type="kafka",
            queue_name=queue_topic,
        )

    async def get_queue_configuration(self, queue_type: str, queue_name: str):
        return await self.client.get_queue_config(queue_type, queue_name)

    async def put_queue_configuration(self, queue_configuration: QueueConfiguration):
        return await self.client.put_queue_config(
            body=queue_configuration.get_worker_configuration(),  # type: ignore[arg-type]
            queue_name=queue_configuration.queue_name,
            queue_type=queue_configuration.queue_type,
        )
