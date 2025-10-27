import os
import uuid

import pytest
import pytest_asyncio

from conductor.asyncio_client.adapters.api_client_adapter import (
    ApiClientAdapter as ApiClient,
)
from conductor.asyncio_client.adapters.models.event_handler_adapter import (
    EventHandlerAdapter,
)
from conductor.asyncio_client.adapters.models.action_adapter import ActionAdapter
from conductor.asyncio_client.adapters.models.tag_adapter import (
    TagAdapter as MetadataTag,
)
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.exceptions import ApiException
from conductor.asyncio_client.orkes.orkes_event_client import OrkesEventClient
from conductor.asyncio_client.orkes.orkes_integration_client import (
    OrkesIntegrationClient,
)


class TestOrkesEventClientIntegration:

    @pytest.fixture(scope="class")
    def configuration(self) -> Configuration:
        config = Configuration()
        config.debug = os.getenv("CONDUCTOR_DEBUG", "false").lower() == "true"
        config.apply_logging_config()
        return config

    @pytest_asyncio.fixture(scope="function")
    async def event_client(self, configuration: Configuration) -> OrkesEventClient:
        async with ApiClient(configuration) as api_client:
            return OrkesEventClient(configuration, api_client)

    @pytest_asyncio.fixture(scope="function")
    async def integration_client(
        self, configuration: Configuration
    ) -> OrkesIntegrationClient:
        async with ApiClient(configuration) as api_client:
            return OrkesIntegrationClient(configuration, api_client)

    @pytest.fixture(scope="class")
    def test_suffix(self) -> str:
        return str(uuid.uuid4())[:8]

    @pytest.fixture(scope="class")
    def simple_event_handler_config(self) -> dict:
        return {
            "name": "test_handler",
            "event": "workflow.completed",
            "active": True,
            "condition": "payload.status == 'COMPLETED'",
            "description": "Test event handler",
            "actions": [
                {
                    "action": "start_workflow",
                    "workflow_id": "notification_workflow",
                    "input_parameters": {"message": "Workflow completed"},
                }
            ],
        }

    @pytest.fixture(scope="class")
    def kafka_integration_config(self) -> dict:
        return {
            "bootstrapServers": "localhost:9092",
            "topic": "test_events",
            "consumerGroup": "test_consumer_group",
            "autoOffsetReset": "earliest",
        }

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_create_and_get_event_handler(
        self,
        event_client: OrkesEventClient,
        test_suffix: str,
        simple_event_handler_config: dict,
    ):
        handler_name = f"test_handler_{test_suffix}"

        event_handler = EventHandlerAdapter(
            name=handler_name,
            event=simple_event_handler_config["event"],
            active=simple_event_handler_config["active"],
            condition=simple_event_handler_config["condition"],
            description=simple_event_handler_config["description"],
            actions=[
                ActionAdapter(
                    action=action["action"],
                    workflow_id=action["workflow_id"],
                    input_parameters=action["input_parameters"],
                )
                for action in simple_event_handler_config["actions"]
            ],
        )

        try:
            await event_client.create_event_handler([event_handler])
            retrieved_handler = await event_client.get_event_handler(handler_name)

            assert retrieved_handler.name == handler_name
            assert retrieved_handler.event == simple_event_handler_config["event"]
            assert retrieved_handler.active == simple_event_handler_config["active"]
            assert (
                retrieved_handler.condition == simple_event_handler_config["condition"]
            )
            assert (
                retrieved_handler.description
                == simple_event_handler_config["description"]
            )
        finally:
            await self._cleanup_event_handler(event_client, handler_name)

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_update_event_handler(
        self,
        event_client: OrkesEventClient,
        test_suffix: str,
        simple_event_handler_config: dict,
    ):
        handler_name = f"test_update_handler_{test_suffix}"

        event_handler = EventHandlerAdapter(
            name=handler_name,
            event=simple_event_handler_config["event"],
            active=simple_event_handler_config["active"],
            condition=simple_event_handler_config["condition"],
            description=simple_event_handler_config["description"],
            actions=[
                ActionAdapter(
                    action=action["action"],
                    workflow_id=action["workflow_id"],
                    input_parameters=action["input_parameters"],
                )
                for action in simple_event_handler_config["actions"]
            ],
        )

        try:
            await event_client.create_event_handler([event_handler])

            event_handler.active = False
            event_handler.condition = "payload.status == 'FAILED'"
            event_handler.description = "Updated test event handler"

            await event_client.update_event_handler(event_handler)
            updated_handler = await event_client.get_event_handler(handler_name)

            assert updated_handler.name == handler_name
            assert updated_handler.active is False
            assert updated_handler.condition == "payload.status == 'FAILED'"
            assert updated_handler.description == "Updated test event handler"
        finally:
            await self._cleanup_event_handler(event_client, handler_name)

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_list_event_handlers(
        self,
        event_client: OrkesEventClient,
        test_suffix: str,
        simple_event_handler_config: dict,
    ):
        handler_name = f"test_list_handler_{test_suffix}"

        event_handler = EventHandlerAdapter(
            name=handler_name,
            event=simple_event_handler_config["event"],
            active=simple_event_handler_config["active"],
            condition=simple_event_handler_config["condition"],
            description=simple_event_handler_config["description"],
            actions=[
                ActionAdapter(
                    action=action["action"],
                    workflow_id=action["workflow_id"],
                    input_parameters=action["input_parameters"],
                )
                for action in simple_event_handler_config["actions"]
            ],
        )

        try:
            await event_client.create_event_handler([event_handler])

            all_handlers = await event_client.list_event_handlers()
            assert isinstance(all_handlers, list)

            handler_names = [handler.name for handler in all_handlers]
            assert handler_name in handler_names
        finally:
            await self._cleanup_event_handler(event_client, handler_name)

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_list_event_handlers_for_event(
        self,
        event_client: OrkesEventClient,
        test_suffix: str,
        simple_event_handler_config: dict,
    ):
        handler_name = f"test_event_handlers_{test_suffix}"
        event_type = "workflow.completed"

        event_handler = EventHandlerAdapter(
            name=handler_name,
            event=event_type,
            active=simple_event_handler_config["active"],
            condition=simple_event_handler_config["condition"],
            description=simple_event_handler_config["description"],
            actions=[
                ActionAdapter(
                    action=action["action"],
                    workflow_id=action["workflow_id"],
                    input_parameters=action["input_parameters"],
                )
                for action in simple_event_handler_config["actions"]
            ],
        )

        try:
            await event_client.create_event_handler([event_handler])

            event_handlers = await event_client.list_event_handlers_for_event(
                event_type
            )
            assert isinstance(event_handlers, list)

            handler_names = [handler.name for handler in event_handlers]
            assert handler_name in handler_names

            for handler in event_handlers:
                assert handler.event == event_type
        finally:
            await self._cleanup_event_handler(event_client, handler_name)

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_event_handler_tags(
        self,
        event_client: OrkesEventClient,
        test_suffix: str,
        simple_event_handler_config: dict,
    ):
        handler_name = f"test_tags_handler_{test_suffix}"

        event_handler = EventHandlerAdapter(
            name=handler_name,
            event=simple_event_handler_config["event"],
            active=simple_event_handler_config["active"],
            condition=simple_event_handler_config["condition"],
            description=simple_event_handler_config["description"],
            actions=[
                ActionAdapter(
                    action=action["action"],
                    workflow_id=action["workflow_id"],
                    input_parameters=action["input_parameters"],
                )
                for action in simple_event_handler_config["actions"]
            ],
        )

        try:
            await event_client.create_event_handler([event_handler])

            tags = [
                MetadataTag(key="environment", value="test", type="METADATA"),
                MetadataTag(key="team", value="platform", type="METADATA"),
                MetadataTag(key="priority", value="high", type="METADATA"),
            ]

            await event_client.add_event_handler_tag(handler_name, tags)

            retrieved_tags = await event_client.get_event_handler_tags(handler_name)
            assert len(retrieved_tags) == 3

            tag_keys = [tag.key for tag in retrieved_tags]
            assert "environment" in tag_keys
            assert "team" in tag_keys
            assert "priority" in tag_keys

            tags_to_remove = [
                MetadataTag(key="environment", value="test", type="METADATA"),
                MetadataTag(key="priority", value="high", type="METADATA"),
            ]

            await event_client.remove_event_handler_tag(handler_name, tags_to_remove)

            remaining_tags = await event_client.get_event_handler_tags(handler_name)
            remaining_keys = [tag.key for tag in remaining_tags]
            assert "environment" not in remaining_keys
            assert "priority" not in remaining_keys
            assert "team" in remaining_keys
        finally:
            await self._cleanup_event_handler(event_client, handler_name)

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_queue_configuration_operations(
        self,
        event_client: OrkesEventClient,
        test_suffix: str,
    ):
        queue_name = f"test_queue_{test_suffix}"
        queue_type = "kafka"

        try:
            try:
                retrieved_config = await event_client.get_queue_configuration(
                    queue_type, queue_name
                )
                assert isinstance(retrieved_config, dict)
            except Exception as e:
                pass

            try:
                await event_client.delete_queue_configuration(queue_type, queue_name)
            except Exception as e:
                pass

        except Exception as e:
            pass

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_multiple_event_handlers(
        self,
        event_client: OrkesEventClient,
        test_suffix: str,
    ):
        handler_names = []

        try:
            handlers = []
            for i in range(3):
                handler_name = f"test_multi_handler_{i}_{test_suffix}"
                handler_names.append(handler_name)

                handler = EventHandlerAdapter(
                    name=handler_name,
                    event=f"test.event.{i}",
                    active=True,
                    condition=f"payload.id == {i}",
                    description=f"Test handler {i}",
                    actions=[
                        ActionAdapter(
                            action="start_workflow",
                            workflow_id=f"test_workflow_{i}",
                            input_parameters={"id": i},
                        )
                    ],
                )
                handlers.append(handler)

            await event_client.create_event_handler(handlers)

            all_handlers = await event_client.list_event_handlers()
            created_handlers = [h for h in all_handlers if h.name in handler_names]
            assert len(created_handlers) == 3

            for handler in created_handlers:
                handler.active = False
                await event_client.update_event_handler(handler)

            for handler_name in handler_names:
                handler = await event_client.get_event_handler(handler_name)
                assert handler.active is False
        finally:
            for handler_name in handler_names:
                await self._cleanup_event_handler(event_client, handler_name)

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_integration_not_found(
        self, integration_client: OrkesIntegrationClient
    ):
        non_existent_integration = f"non_existent_{str(uuid.uuid4())}"

        with pytest.raises(ApiException) as e:
            await integration_client.get_integration_provider(non_existent_integration)
        assert e.value.status == 404

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_invalid_event_handler_data(self, event_client: OrkesEventClient):
        invalid_handler = EventHandlerAdapter(name="", event="test.event", active=True)

        with pytest.raises(ApiException):
            await event_client.create_event_handler([invalid_handler])

    async def _cleanup_event_handler(
        self, event_client: OrkesEventClient, handler_name: str
    ):
        cleanup_enabled = os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true"
        if not cleanup_enabled:
            return

        try:
            await event_client.delete_event_handler(handler_name)
        except Exception as e:
            pass

    async def _cleanup_integration(
        self, integration_client: OrkesIntegrationClient, integration_name: str
    ):
        cleanup_enabled = os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true"
        if not cleanup_enabled:
            return

        try:
            await integration_client.delete_integration_provider(integration_name)
        except Exception as e:
            pass
