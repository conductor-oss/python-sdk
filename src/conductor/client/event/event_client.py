from __future__ import annotations

from typing import List

from conductor.client.event.queue.queue_configuration import QueueConfiguration
from conductor.client.adapters.models.tag_adapter import TagAdapter
from conductor.client.http.api import EventResourceApi
from conductor.client.http.api_client import ApiClient


class EventClient:
    def __init__(self, api_client: ApiClient):
        self.client = EventResourceApi(api_client)

    def delete_queue_configuration(
        self, queue_configuration: QueueConfiguration
    ) -> None:
        return self.client.delete_queue_config(
            queue_name=queue_configuration.queue_name,
            queue_type=queue_configuration.queue_type,
        )

    def get_kafka_queue_configuration(self, queue_topic: str) -> QueueConfiguration:
        return self.get_queue_configuration(
            queue_type="kafka",
            queue_name=queue_topic,
        )

    def get_queue_configuration(self, queue_type: str, queue_name: str):
        return self.client.get_queue_config(queue_type, queue_name)

    def put_queue_configuration(self, queue_configuration: QueueConfiguration):
        return self.client.put_queue_config(
            body=queue_configuration.get_worker_configuration(),
            queue_name=queue_configuration.queue_name,
            queue_type=queue_configuration.queue_type,
        )

    def get_event_handler_tags(self, name: str) -> List[TagAdapter]:
        """Get tags for an event handler.

        Retrieves all tags associated with a specific event handler.
        Tags are used for organizing and categorizing event handlers.

        Parameters:
        -----------
        name : str
            The name of the event handler

        Returns:
        --------
        List[TagAdapter]
            List of tags associated with the event handler

        Example:
        --------
        ```python
        # Get tags for an event handler
        tags = event_client.get_event_handler_tags("workflow_trigger")
        for tag in tags:
            print(f"Tag: {tag.key} = {tag.value}")
        ```
        """
        return self.client.get_tags_for_event_handler(name=name)

    def add_event_handler_tag(self, name: str, tags: List[TagAdapter]) -> None:
        """Add tags to an event handler.

        Associates one or more tags with an event handler for organization and categorization.

        Parameters:
        -----------
        name : str
            The name of the event handler
        tags : List[TagAdapter]
            List of tags to add to the event handler

        Example:
        --------
        ```python
        from conductor.client.adapters.models.tag_adapter import TagAdapter

        # Add tags to an event handler
        tags = [
            TagAdapter(key="environment", value="production"),
            TagAdapter(key="team", value="platform"),
            TagAdapter(key="priority", value="high")
        ]

        event_client.add_event_handler_tag("workflow_trigger", tags)
        ```
        """
        # Note: Sync API uses (tags, name) parameter order due to swagger-codegen placing
        # body params before path params. Async API uses (name=name, tag=tags) instead.
        return self.client.put_tag_for_event_handler(tags, name)

    def remove_event_handler_tag(self, name: str, tags: List[TagAdapter]) -> None:
        """Remove tags from an event handler.

        Removes one or more tags from an event handler.

        Parameters:
        -----------
        name : str
            The name of the event handler
        tags : List[TagAdapter]
            List of tags to remove from the event handler

        Example:
        --------
        ```python
        from conductor.client.adapters.models.tag_adapter import TagAdapter

        # Remove specific tags from an event handler
        tags_to_remove = [
            TagAdapter(key="environment", value="production"),
            TagAdapter(key="priority", value="high")
        ]

        event_client.remove_event_handler_tag("workflow_trigger", tags_to_remove)
        ```
        """
        # Note: Sync API uses (tags, name) parameter order due to swagger-codegen placing
        # body params before path params. Async API uses (name=name, tag=tags) instead.
        return self.client.delete_tag_for_event_handler(tags, name)
