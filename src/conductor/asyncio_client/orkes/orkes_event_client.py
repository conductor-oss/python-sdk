from __future__ import annotations

from typing import Any, Dict, List

from conductor.asyncio_client.adapters.models.connectivity_test_input_adapter import (
    ConnectivityTestInputAdapter,
)
from conductor.asyncio_client.adapters.models.connectivity_test_result_adapter import (
    ConnectivityTestResultAdapter,
)
from conductor.asyncio_client.adapters.models.event_handler_adapter import EventHandlerAdapter
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient


class OrkesEventClient(OrkesBaseClient):
    """Event management client for Orkes Conductor platform.

    Provides comprehensive event handling capabilities including event handler
    management, tag operations, queue configuration, and event execution monitoring.
    """

    # Event Handler Operations
    async def create_event_handler(
        self, event_handler: List[EventHandlerAdapter], **kwargs
    ) -> None:
        """Create a new event handler.

        Creates one or more event handlers that will be triggered by specific events.
        Event handlers define what actions to take when certain events occur in the system.

        Parameters:
        -----------
        event_handler : List[EventHandlerAdapter]
            List of event handler configurations to create

        Example:
        --------
        ```python
        from conductor.asyncio_client.adapters.models.event_handler_adapter import EventHandlerAdapter
        from conductor.asyncio_client.adapters.models.action_adapter import ActionAdapter

        # Create an event handler
        event_handler = EventHandlerAdapter(
            name="workflow_trigger",
            event="workflow.completed",
            active=True,
            condition="payload.status == 'COMPLETED'",
            actions=[
                ActionAdapter(
                    action="start_workflow",
                    workflow_id="notification_workflow",
                    input_parameters={"message": "Workflow completed successfully"}
                )
            ]
        )

        await event_client.create_event_handler([event_handler])
        ```
        """
        return await self._event_api.add_event_handler(event_handler=event_handler, **kwargs)

    async def get_event_handler(self, name: str, **kwargs) -> EventHandlerAdapter:
        """Get event handler by name.

        Retrieves a specific event handler configuration by its name.

        Parameters:
        -----------
        name : str
            The name of the event handler to retrieve

        Returns:
        --------
        EventHandlerAdapter
            The event handler configuration

        Example:
        --------
        ```python
        # Get a specific event handler
        handler = await event_client.get_event_handler("workflow_trigger")
        print(f"Handler event: {handler.event}")
        print(f"Handler active: {handler.active}")
        ```
        """
        return await self._event_api.get_event_handler_by_name(name=name, **kwargs)

    async def list_event_handlers(self, **kwargs) -> List[EventHandlerAdapter]:
        """List all event handlers.

        Retrieves all event handlers configured in the system.

        Returns:
        --------
        List[EventHandlerAdapter]
            List of all event handler configurations

        Example:
        --------
        ```python
        # List all event handlers
        handlers = await event_client.list_event_handlers()
        for handler in handlers:
            print(f"Handler: {handler.name}, Event: {handler.event}, Active: {handler.active}")
        ```
        """
        return await self._event_api.get_event_handlers(**kwargs)

    async def list_event_handlers_for_event(
        self, event: str, **kwargs
    ) -> List[EventHandlerAdapter]:
        """List event handlers for a specific event.

        Retrieves all event handlers that are configured to respond to a specific event type.

        Parameters:
        -----------
        event : str
            The event type to filter handlers by (e.g., "workflow.completed", "task.failed")

        Returns:
        --------
        List[EventHandlerAdapter]
            List of event handlers that respond to the specified event

        Example:
        --------
        ```python
        # Get handlers for workflow completion events
        handlers = await event_client.list_event_handlers_for_event("workflow.completed")
        print(f"Found {len(handlers)} handlers for workflow.completed events")

        # Get handlers for task failure events
        failure_handlers = await event_client.list_event_handlers_for_event("task.failed")
        ```
        """
        return await self._event_api.get_event_handlers_for_event(event=event, **kwargs)

    async def update_event_handler(self, event_handler: EventHandlerAdapter, **kwargs) -> None:
        """Update an existing event handler.

        Updates the configuration of an existing event handler.
        The handler is identified by its name field.

        Parameters:
        -----------
        event_handler : EventHandlerAdapter
            Event handler configuration to update

        Example:
        --------
        ```python
        # Update an existing event handler
        handler = await event_client.get_event_handler("workflow_trigger")
        handler.active = False  # Disable the handler
        handler.condition = "payload.status == 'COMPLETED' AND payload.priority == 'HIGH'"

        await event_client.update_event_handler(handler)
        ```
        """
        return await self._event_api.update_event_handler(event_handler=event_handler, **kwargs)

    async def delete_event_handler(self, name: str, **kwargs) -> None:
        """Delete an event handler by name.

        Permanently removes an event handler from the system.

        Parameters:
        -----------
        name : str
            The name of the event handler to delete

        Example:
        --------
        ```python
        # Delete an event handler
        await event_client.delete_event_handler("old_workflow_trigger")
        print("Event handler deleted successfully")
        ```
        """
        return await self._event_api.remove_event_handler_status(name=name, **kwargs)

    # Event Handler Tag Operations
    async def get_event_handler_tags(self, name: str, **kwargs) -> List[TagAdapter]:
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
        tags = await event_client.get_event_handler_tags("workflow_trigger")
        for tag in tags:
            print(f"Tag: {tag.key} = {tag.value}")
        ```
        """
        return await self._event_api.get_tags_for_event_handler(name=name, **kwargs)

    async def add_event_handler_tag(self, name: str, tags: List[TagAdapter], **kwargs) -> None:
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
        from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

        # Add tags to an event handler
        tags = [
            TagAdapter(key="environment", value="production"),
            TagAdapter(key="team", value="platform"),
            TagAdapter(key="priority", value="high")
        ]

        await event_client.add_event_handler_tag("workflow_trigger", tags)
        ```
        """
        # Note: Async API uses (name=name, tag=tags) keyword args to match the server signature.
        # Sync API uses (tags, name) positional args due to swagger-codegen parameter ordering.
        return await self._event_api.put_tag_for_event_handler(name=name, tag=tags, **kwargs)

    async def remove_event_handler_tag(self, name: str, tags: List[TagAdapter], **kwargs) -> None:
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
        from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

        # Remove specific tags from an event handler
        tags_to_remove = [
            TagAdapter(key="environment", value="production"),
            TagAdapter(key="priority", value="high")
        ]

        await event_client.remove_event_handler_tag("workflow_trigger", tags_to_remove)
        ```
        """
        # Note: Async API uses (name=name, tag=tags) keyword args to match the server signature.
        # Sync API uses (tags, name) positional args due to swagger-codegen parameter ordering.
        return await self._event_api.delete_tag_for_event_handler(name=name, tag=tags, **kwargs)

    # Queue Configuration Operations
    async def get_queue_configuration(
        self, queue_type: str, queue_name: str, **kwargs
    ) -> Dict[str, object]:
        """Get queue configuration.

        Retrieves the configuration for a specific event queue.

        Parameters:
        -----------
        queue_type : str
            The type of queue (e.g., "kafka", "sqs", "rabbitmq")
        queue_name : str
            The name of the queue

        Returns:
        --------
        Dict[str, object]
            Queue configuration settings

        Example:
        --------
        ```python
        # Get Kafka queue configuration
        config = await event_client.get_queue_configuration("kafka", "workflow_events")
        print(f"Bootstrap servers: {config.get('bootstrapServers')}")
        print(f"Topic: {config.get('topic')}")
        ```
        """
        return await self._event_api.get_queue_config(
            queue_type=queue_type, queue_name=queue_name, **kwargs
        )

    async def delete_queue_configuration(self, queue_type: str, queue_name: str, **kwargs) -> None:
        """Delete queue configuration.

        Removes the configuration for an event queue.

        Parameters:
        -----------
        queue_type : str
            The type of queue (e.g., "kafka", "sqs", "rabbitmq")
        queue_name : str
            The name of the queue

        Example:
        --------
        ```python
        # Delete a queue configuration
        await event_client.delete_queue_configuration("kafka", "old_workflow_events")
        print("Queue configuration deleted")
        ```
        """
        return await self._event_api.delete_queue_config(
            queue_type=queue_type, queue_name=queue_name, **kwargs
        )

    async def get_queue_names(self, **kwargs) -> Dict[str, str]:
        """Get all queue names.

        Retrieves all queue names configured in the system.

        Returns:
        --------
        Dict[str, str]
            Dictionary of queue names and their types
        """
        return await self._event_api.get_queue_names(**kwargs)

    async def handle_incoming_event(
        self, request_body: Dict[str, Dict[str, Any]], **kwargs
    ) -> None:
        """Handle an incoming event.

        Handles an incoming event from the system.

        Parameters:
        -----------
        request_body : Dict[str, Dict[str, Any]]
            The incoming event request body
        """
        return await self._event_api.handle_incoming_event(request_body=request_body, **kwargs)

    async def put_queue_configuration(
        self, queue_type: str, queue_name: str, body: str, **kwargs
    ) -> None:
        """Put queue configuration.

        Updates the configuration for an event queue.

        Parameters:
        -----------
        queue_type : str
            The type of queue (e.g., "kafka", "sqs", "rabbitmq")
        queue_name : str
            The name of the queue
        body : str
            The body of the queue configuration
        """
        return await self._event_api.put_queue_config(
            queue_type=queue_type, queue_name=queue_name, body=body, **kwargs
        )

    async def test(self, **kwargs) -> EventHandlerAdapter:
        """Test the event handler.

        Tests the event handler.

        Parameters:
        -----------
        """
        return await self._event_api.test(**kwargs)

    async def test_connectivity(
        self, connectivity_test_input: ConnectivityTestInputAdapter, **kwargs
    ) -> ConnectivityTestResultAdapter:
        """Test connectivity.

        Tests the connectivity of the event handler.

        Parameters:
        -----------
        connectivity_test_input : ConnectivityTestInputAdapter
            The connectivity test input
        """
        return await self._event_api.test_connectivity(
            connectivity_test_input=connectivity_test_input, **kwargs
        )
