import os
import uuid

import pytest

from conductor.client.configuration.configuration import Configuration
from conductor.client.codegen.rest import ApiException
from conductor.client.adapters.models.event_handler_adapter import EventHandlerAdapter
from conductor.client.adapters.models.tag_adapter import TagAdapter
from conductor.client.adapters.models.action_adapter import ActionAdapter
from conductor.client.codegen.models.start_workflow import StartWorkflow
from conductor.client.orkes.orkes_event_client import OrkesEventClient


class TestOrkesEventClientIntegration:
    """
    Integration tests for OrkesEventClient.

    Environment Variables:
    - CONDUCTOR_SERVER_URL: Base URL for Conductor server (default: http://localhost:8080/api)
    - CONDUCTOR_AUTH_KEY: Authentication key for Orkes
    - CONDUCTOR_AUTH_SECRET: Authentication secret for Orkes
    - CONDUCTOR_UI_SERVER_URL: UI server URL (optional)
    - CONDUCTOR_TEST_TIMEOUT: Test timeout in seconds (default: 30)
    - CONDUCTOR_TEST_CLEANUP: Whether to cleanup test resources (default: true)
    """

    @pytest.fixture(scope="class")
    def configuration(self) -> Configuration:
        config = Configuration()
        config.debug = os.getenv("CONDUCTOR_DEBUG", "false").lower() == "true"
        config.apply_logging_config()
        return config

    @pytest.fixture(scope="class")
    def event_client(self, configuration: Configuration) -> OrkesEventClient:
        return OrkesEventClient(configuration)

    @pytest.fixture(scope="class")
    def test_suffix(self) -> str:
        return str(uuid.uuid4())[:8]

    @pytest.fixture(scope="class")
    def test_event_handler_name(self, test_suffix: str) -> str:
        return f"test_event_handler_{test_suffix}"

    @pytest.fixture(scope="class")
    def simple_event_handler(self, test_event_handler_name: str) -> EventHandlerAdapter:
        return EventHandlerAdapter(
            name=test_event_handler_name,
            event="workflow.completed",
            active=True,
            condition="payload.status == 'COMPLETED'",
            actions=[
                ActionAdapter(
                    action="start_workflow",
                    start_workflow=StartWorkflow(
                        name="notification_workflow",
                        input={"message": "Workflow completed successfully"}
                    )
                )
            ]
        )

    @pytest.fixture(scope="class")
    def complex_event_handler(self, test_suffix: str) -> EventHandlerAdapter:
        return EventHandlerAdapter(
            name=f"test_complex_handler_{test_suffix}",
            event="task.failed",
            active=True,
            condition="payload.taskType == 'HTTP' AND payload.status == 'FAILED'",
            actions=[
                ActionAdapter(
                    action="start_workflow",
                    start_workflow=StartWorkflow(
                        name="error_notification_workflow",
                        input={
                            "error_message": "Task failed",
                            "task_id": "${payload.taskId}",
                            "retry_count": "${payload.retryCount}"
                        }
                    )
                )
            ]
        )

    @pytest.fixture(scope="class")
    def test_tags(self) -> list:
        return [
            TagAdapter(key="environment", value="test"),
            TagAdapter(key="team", value="platform"),
            TagAdapter(key="priority", value="high")
        ]

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_event_handler_lifecycle_simple(
        self,
        event_client: OrkesEventClient,
        test_event_handler_name: str,
        simple_event_handler: EventHandlerAdapter,
    ):
        try:
            event_client.create_event_handler([simple_event_handler])

            retrieved_handler = event_client.get_event_handler(test_event_handler_name)
            assert retrieved_handler.name == test_event_handler_name
            assert retrieved_handler.event == "workflow.completed"
            assert retrieved_handler.active is True
            assert retrieved_handler.condition == "payload.status == 'COMPLETED'"
            assert len(retrieved_handler.actions) == 1
            assert retrieved_handler.actions[0].action == "start_workflow"

            handlers = event_client.list_event_handlers()
            handler_names = [h.name for h in handlers]
            assert test_event_handler_name in handler_names

            event_handlers = event_client.list_event_handlers_for_event("workflow.completed")
            event_handler_names = [h.name for h in event_handlers]
            assert test_event_handler_name in event_handler_names

        except Exception as e:
            print(f"Exception in test_event_handler_lifecycle_simple: {str(e)}")
            raise
        finally:
            try:
                event_client.delete_event_handler(test_event_handler_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup event handler {test_event_handler_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_event_handler_lifecycle_complex(
        self,
        event_client: OrkesEventClient,
        test_suffix: str,
        complex_event_handler: EventHandlerAdapter,
    ):
        handler_name = complex_event_handler.name
        try:
            event_client.create_event_handler([complex_event_handler])

            retrieved_handler = event_client.get_event_handler(handler_name)
            assert retrieved_handler.name == handler_name
            assert retrieved_handler.event == "task.failed"
            assert retrieved_handler.active is True
            assert "taskType == 'HTTP'" in retrieved_handler.condition
            assert len(retrieved_handler.actions) == 1
            assert retrieved_handler.actions[0].start_workflow.name == "error_notification_workflow"

        except Exception as e:
            print(f"Exception in test_event_handler_lifecycle_complex: {str(e)}")
            raise
        finally:
            try:
                event_client.delete_event_handler(handler_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup event handler {handler_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_event_handler_with_tags(
        self,
        event_client: OrkesEventClient,
        test_suffix: str,
        simple_event_handler: EventHandlerAdapter,
        test_tags: list,
    ):
        handler_name = f"test_tagged_handler_{test_suffix}"
        try:
            handler = EventHandlerAdapter(
                name=handler_name,
                event="workflow.completed",
                active=True,
                condition="payload.status == 'COMPLETED'",
                actions=[
                    ActionAdapter(
                        action="start_workflow",
                        start_workflow=StartWorkflow(
                            name="notification_workflow",
                            input={"message": "Workflow completed"}
                        )
                    )
                ]
            )
            event_client.create_event_handler([handler])

            event_client.add_event_handler_tag(handler_name, test_tags)

            retrieved_tags = event_client.get_event_handler_tags(handler_name)
            assert len(retrieved_tags) == 3
            tag_keys = [tag.key for tag in retrieved_tags]
            assert "environment" in tag_keys
            assert "team" in tag_keys
            assert "priority" in tag_keys

            tags_to_delete = [TagAdapter(key="priority", value="high")]
            event_client.remove_event_handler_tag(handler_name, tags_to_delete)

            retrieved_tags_after_delete = event_client.get_event_handler_tags(handler_name)
            remaining_tag_keys = [tag.key for tag in retrieved_tags_after_delete]
            assert "priority" not in remaining_tag_keys
            assert len(retrieved_tags_after_delete) == 2

        except Exception as e:
            print(f"Exception in test_event_handler_with_tags: {str(e)}")
            raise
        finally:
            try:
                event_client.delete_event_handler(handler_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup event handler {handler_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_event_handler_update(
        self,
        event_client: OrkesEventClient,
        test_suffix: str,
        simple_event_handler: EventHandlerAdapter,
    ):
        handler_name = f"test_handler_update_{test_suffix}"
        try:
            initial_handler = EventHandlerAdapter(
                name=handler_name,
                event="workflow.completed",
                active=True,
                condition="payload.status == 'COMPLETED'",
                actions=[
                    ActionAdapter(
                        action="start_workflow",
                        start_workflow=StartWorkflow(
                            name="notification_workflow",
                            input={"message": "Workflow completed"}
                        )
                    )
                ]
            )
            event_client.create_event_handler([initial_handler])

            retrieved_handler = event_client.get_event_handler(handler_name)
            assert retrieved_handler.active is True
            assert retrieved_handler.condition == "payload.status == 'COMPLETED'"

            updated_handler = EventHandlerAdapter(
                name=handler_name,
                event="workflow.completed",
                active=False,
                condition="payload.status == 'COMPLETED' AND payload.priority == 'HIGH'",
                actions=[
                    ActionAdapter(
                        action="start_workflow",
                        start_workflow=StartWorkflow(
                            name="priority_notification_workflow",
                            input={"message": "High priority workflow completed"}
                        )
                    )
                ]
            )
            event_client.update_event_handler(updated_handler)

            updated_retrieved_handler = event_client.get_event_handler(handler_name)
            assert updated_retrieved_handler.active is False
            assert "priority == 'HIGH'" in updated_retrieved_handler.condition
            assert updated_retrieved_handler.actions[0].start_workflow.name == "priority_notification_workflow"

        except Exception as e:
            print(f"Exception in test_event_handler_update: {str(e)}")
            raise
        finally:
            try:
                event_client.delete_event_handler(handler_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup event handler {handler_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_queue_configuration_operations(
        self,
        event_client: OrkesEventClient,
        test_suffix: str,
    ):
        queue_type = "kafka"
        queue_name = f"test_queue_{test_suffix}"
        
        try:
            config = event_client.get_queue_configuration(queue_type, queue_name)
            assert isinstance(config, dict)

        except Exception as e:
            print(f"Exception in test_queue_configuration_operations: {str(e)}")
            raise

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_concurrent_event_handler_operations(
        self,
        event_client: OrkesEventClient,
        test_suffix: str,
    ):
        try:
            import threading
            import time

            results = []
            errors = []
            created_handlers = []
            cleanup_lock = threading.Lock()

            def create_and_delete_handler(handler_suffix: str):
                handler_name = None
                try:
                    handler_name = f"concurrent_handler_{handler_suffix}"
                    handler = EventHandlerAdapter(
                        name=handler_name,
                        event="workflow.completed",
                        active=True,
                        condition="payload.status == 'COMPLETED'",
                        actions=[
                            ActionAdapter(
                                action="start_workflow",
                                start_workflow=StartWorkflow(
                                    name="notification_workflow",
                                    input={"message": "Workflow completed"}
                                )
                            )
                        ]
                    )
                    event_client.create_event_handler([handler])

                    with cleanup_lock:
                        created_handlers.append(handler_name)

                    time.sleep(0.1)

                    retrieved_handler = event_client.get_event_handler(handler_name)
                    assert retrieved_handler.name == handler_name

                    if os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true":
                        try:
                            event_client.delete_event_handler(handler_name)
                            with cleanup_lock:
                                if handler_name in created_handlers:
                                    created_handlers.remove(handler_name)
                        except Exception as cleanup_error:
                            print(
                                f"Warning: Failed to cleanup handler {handler_name} in thread: {str(cleanup_error)}"
                            )

                    results.append(f"handler_{handler_suffix}_success")
                except Exception as e:
                    errors.append(f"handler_{handler_suffix}_error: {str(e)}")
                    if handler_name and handler_name not in created_handlers:
                        with cleanup_lock:
                            created_handlers.append(handler_name)

            threads = []
            for i in range(3):
                thread = threading.Thread(
                    target=create_and_delete_handler, args=(f"{test_suffix}_{i}",)
                )
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            assert (
                len(results) == 3
            ), f"Expected 3 successful operations, got {len(results)}. Errors: {errors}"
            assert len(errors) == 0, f"Unexpected errors: {errors}"

        except Exception as e:
            print(f"Exception in test_concurrent_event_handler_operations: {str(e)}")
            raise
        finally:
            for handler_name in created_handlers:
                try:
                    event_client.delete_event_handler(handler_name)
                except Exception as e:
                    print(f"Warning: Failed to delete handler {handler_name}: {str(e)}")

    def _perform_comprehensive_cleanup(
        self, event_client: OrkesEventClient, created_resources: dict
    ):
        cleanup_enabled = os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true"
        if not cleanup_enabled:
            return

        for handler_name in created_resources["handlers"]:
            try:
                event_client.delete_event_handler(handler_name)
            except Exception as e:
                print(f"Warning: Failed to delete handler {handler_name}: {str(e)}")

        remaining_handlers = []
        for handler_name in created_resources["handlers"]:
            try:
                retrieved_handler = event_client.get_event_handler(handler_name)
                if retrieved_handler is not None:
                    remaining_handlers.append(handler_name)
            except ApiException as e:
                if e.code == 404:
                    pass
                else:
                    remaining_handlers.append(handler_name)
            except Exception:
                remaining_handlers.append(handler_name)

        if remaining_handlers:
            print(
                f"Warning: {len(remaining_handlers)} handlers could not be verified as deleted: {remaining_handlers}"
            )
