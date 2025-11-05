from __future__ import annotations

from typing import Dict, List

from conductor.client.adapters.models.event_handler_adapter import EventHandlerAdapter
from conductor.client.adapters.models.tag_adapter import TagAdapter
from conductor.client.http.models.connectivity_test_input import ConnectivityTestInput
from conductor.client.http.models.connectivity_test_result import ConnectivityTestResult
from conductor.client.http.models.event_handler import EventHandler
from conductor.client.orkes.orkes_base_client import OrkesBaseClient


class OrkesEventClient(OrkesBaseClient):
    # Event Handler Operations
    def create_event_handler(self, event_handler: List[EventHandlerAdapter]) -> None:
        """Create a new event handler.

        Creates one or more event handlers that will be triggered by specific events.
        Event handlers define what actions to take when certain events occur in the system.

        Args:
            event_handler: List of event handler configurations to create

        Returns:
            None

        Example:
            ```python
            from conductor.client.adapters.models.event_handler_adapter import EventHandlerAdapter
            from conductor.client.adapters.models.action_adapter import ActionAdapter

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

            event_client.create_event_handler([event_handler])
            ```
        """
        return self._event_api.add_event_handler(event_handler)

    def get_event_handler(self, name: str) -> EventHandlerAdapter:
        """Get event handler by name.

        Retrieves a specific event handler configuration by its name.

        Args:
            name: The name of the event handler to retrieve

        Returns:
            EventHandlerAdapter instance with the event handler configuration

        Example:
            ```python
            # Get a specific event handler
            handler = event_client.get_event_handler("workflow_trigger")
            print(f"Handler event: {handler.event}")
            print(f"Handler active: {handler.active}")
            ```
        """
        return self._event_api.get_event_handler_by_name(name=name)

    def list_event_handlers(self) -> List[EventHandlerAdapter]:
        """List all event handlers.

        Retrieves all event handlers configured in the system.

        Returns:
            List of EventHandlerAdapter instances

        Example:
            ```python
            # List all event handlers
            handlers = event_client.list_event_handlers()
            for handler in handlers:
                print(f"Handler: {handler.name}, Event: {handler.event}, Active: {handler.active}")
            ```
        """
        return self._event_api.get_event_handlers()

    def list_event_handlers_for_event(self, event: str) -> List[EventHandlerAdapter]:
        """List event handlers for a specific event.

        Retrieves all event handlers that are configured to respond to a specific event type.

        Args:
            event: The event type to filter handlers by (e.g., "workflow.completed", "task.failed")

        Returns:
            List of EventHandlerAdapter instances that respond to the specified event

        Example:
            ```python
            # Get handlers for workflow completion events
            handlers = event_client.list_event_handlers_for_event("workflow.completed")
            print(f"Found {len(handlers)} handlers for workflow.completed events")

            # Get handlers for task failure events
            failure_handlers = event_client.list_event_handlers_for_event("task.failed")
            ```
        """
        return self._event_api.get_event_handlers_for_event(event=event)

    def update_event_handler(self, event_handler: EventHandlerAdapter) -> None:
        """Update an existing event handler.

        Updates the configuration of an existing event handler.
        The handler is identified by its name field.

        Args:
            event_handler: Event handler configuration to update

        Returns:
            None

        Example:
            ```python
            # Update an existing event handler
            handler = event_client.get_event_handler("workflow_trigger")
            handler.active = False  # Disable the handler
            handler.condition = "payload.status == 'COMPLETED' AND payload.priority == 'HIGH'"

            event_client.update_event_handler(handler)
            ```
        """
        return self._event_api.update_event_handler(event_handler)

    def delete_event_handler(self, name: str) -> None:
        """Delete an event handler by name.

        Permanently removes an event handler from the system.

        Args:
            name: The name of the event handler to delete

        Returns:
            None

        Example:
            ```python
            # Delete an event handler
            event_client.delete_event_handler("old_workflow_trigger")
            print("Event handler deleted successfully")
            ```
        """
        return self._event_api.remove_event_handler_status(name=name)

    # Event Handler Tag Operations
    def get_event_handler_tags(self, name: str) -> List[TagAdapter]:
        """Get tags for an event handler.

        Retrieves all tags associated with a specific event handler.
        Tags are used for organizing and categorizing event handlers.

        Args:
            name: The name of the event handler

        Returns:
            List of TagAdapter instances

        Example:
            ```python
            # Get tags for an event handler
            tags = event_client.get_event_handler_tags("workflow_trigger")
            for tag in tags:
                print(f"Tag: {tag.key} = {tag.value}")
            ```
        """
        return self._event_api.get_tags_for_event_handler(name=name)

    def add_event_handler_tag(self, name: str, tags: List[TagAdapter]) -> None:
        """Add tags to an event handler.

        Associates one or more tags with an event handler for organization and categorization.

        Args:
            name: The name of the event handler
            tags: List of tags to add to the event handler

        Returns:
            None

        Example:
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
        return self._event_api.put_tag_for_event_handler(tags, name)

    def remove_event_handler_tag(self, name: str, tags: List[TagAdapter]) -> None:
        """Remove tags from an event handler.

        Removes one or more tags from an event handler.

        Args:
            name: The name of the event handler
            tags: List of tags to remove from the event handler

        Returns:
            None

        Example:
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
        return self._event_api.delete_tag_for_event_handler(tags, name)

    # Queue Configuration Operations
    def get_queue_configuration(self, queue_type: str, queue_name: str) -> dict:
        """Get queue configuration.

        Retrieves the configuration for a specific event queue.

        Args:
            queue_type: The type of queue (e.g., "kafka", "sqs", "rabbitmq")
            queue_name: The name of the queue

        Returns:
            Dictionary with queue configuration settings

        Example:
            ```python
            # Get Kafka queue configuration
            config = event_client.get_queue_configuration("kafka", "workflow_events")
            print(f"Bootstrap servers: {config.get('bootstrapServers')}")
            print(f"Topic: {config.get('topic')}")
            ```
        """
        return self._event_api.get_queue_config(queue_type=queue_type, queue_name=queue_name)

    def delete_queue_configuration(self, queue_type: str, queue_name: str) -> None:
        """Delete queue configuration.

        Removes the configuration for an event queue.

        Args:
            queue_type: The type of queue (e.g., "kafka", "sqs", "rabbitmq")
            queue_name: The name of the queue

        Returns:
            None

        Example:
            ```python
            # Delete a queue configuration
            event_client.delete_queue_configuration("kafka", "old_workflow_events")
            print("Queue configuration deleted")
            ```
        """
        return self._event_api.delete_queue_config(queue_type=queue_type, queue_name=queue_name)

    def get_queue_names(self, **kwargs) -> Dict[str, str]:
        """Get all queue names.

        Retrieves a dictionary of all configured queue names and their types.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping queue names to queue types

        Example:
            ```python
            queue_names = event_client.get_queue_names()
            for name, queue_type in queue_names.items():
                print(f"Queue: {name}, Type: {queue_type}")
            ```
        """
        return self._event_api.get_queue_names(**kwargs)

    def handle_incoming_event(self, body: Dict[str, object], **kwargs) -> None:
        """Handle an incoming event.

        Processes an incoming event by routing it to the appropriate event handlers.

        Args:
            body: Event payload as dictionary
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Handle a custom event
            event_payload = {
                "eventType": "order.placed",
                "orderId": "12345",
                "customerId": "cust-999",
                "timestamp": 1234567890
            }

            event_client.handle_incoming_event(event_payload)
            ```
        """
        return self._event_api.handle_incoming_event(body, **kwargs)

    def put_queue_config(self, body: str, queue_type: str, queue_name: str, **kwargs) -> None:
        """Put a queue configuration.

        Creates or updates the configuration for an event queue.

        Args:
            body: Queue configuration as JSON string
            queue_type: The type of queue (e.g., "kafka", "sqs", "rabbitmq")
            queue_name: The name of the queue
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            import json

            # Configure a Kafka queue
            kafka_config = json.dumps({
                "bootstrapServers": "localhost:9092",
                "topic": "workflow_events",
                "consumerGroup": "conductor_events",
                "autoCommit": True
            })

            event_client.put_queue_config(kafka_config, "kafka", "workflow_events")
            ```
        """
        return self._event_api.put_queue_config(body, queue_type, queue_name, **kwargs)

    def test(self, **kwargs) -> EventHandler:
        """Test the event handler.

        Tests an event handler configuration without persisting it.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            EventHandler instance with test results

        Example:
            ```python
            result = event_client.test()
            print(f"Test result: {result}")
            ```
        """
        return self._event_api.test(**kwargs)

    def test_connectivity(self, body: ConnectivityTestInput, **kwargs) -> ConnectivityTestResult:
        """Test the connectivity of an event handler.

        Tests whether an event handler can successfully connect to its configured
        event source (e.g., Kafka, SQS, RabbitMQ).

        Args:
            body: Connectivity test input with connection details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ConnectivityTestResult with test status and details

        Example:
            ```python
            from conductor.client.http.models.connectivity_test_input import ConnectivityTestInput

            # Test Kafka connectivity
            test_input = ConnectivityTestInput(
                queue_type="kafka",
                queue_name="workflow_events",
                configuration={
                    "bootstrapServers": "localhost:9092",
                    "topic": "workflow_events"
                }
            )

            result = event_client.test_connectivity(test_input)
            if result.success:
                print("Connection successful!")
            else:
                print(f"Connection failed: {result.error_message}")
            ```
        """
        return self._event_api.test_connectivity(body, **kwargs)
