import logging
import pytest

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.api.event_resource_api import EventResourceApiAdapter
from conductor.asyncio_client.adapters.models.connectivity_test_input_adapter import (
    ConnectivityTestInputAdapter,
)
from conductor.asyncio_client.adapters.models.connectivity_test_result_adapter import (
    ConnectivityTestResultAdapter,
)
from conductor.asyncio_client.adapters.models.event_handler_adapter import EventHandlerAdapter
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_event_client import OrkesEventClient

EVENT_NAME = "workflow:completed"
HANDLER_NAME = "test_handler"
QUEUE_TYPE = "kafka"
QUEUE_NAME = "test_queue"


@pytest.fixture(scope="module")
def event_client():
    configuration = Configuration("http://localhost:8080/api")
    api_client = ApiClient(configuration)
    return OrkesEventClient(configuration, api_client=api_client)


@pytest.fixture(scope="module")
def event_handler():
    return EventHandlerAdapter(
        name=HANDLER_NAME,
        event=EVENT_NAME,
        active=True,
    )


@pytest.fixture(scope="module")
def tag_list():
    return [
        TagAdapter(key="env", value="prod"),
        TagAdapter(key="team", value="platform"),
    ]


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


def test_init(event_client):
    message = "event_api is not of type EventResourceApiAdapter"
    assert isinstance(event_client.event_api, EventResourceApiAdapter), message


@pytest.mark.asyncio
async def test_create_event_handler(mocker, event_client, event_handler):
    mock = mocker.patch.object(EventResourceApiAdapter, "add_event_handler")
    await event_client.create_event_handler([event_handler])
    mock.assert_called_with(event_handler=[event_handler])


@pytest.mark.asyncio
async def test_get_event_handler(mocker, event_client, event_handler):
    mock = mocker.patch.object(EventResourceApiAdapter, "get_event_handler_by_name")
    mock.return_value = event_handler
    result = await event_client.get_event_handler(HANDLER_NAME)
    mock.assert_called_with(name=HANDLER_NAME)
    assert result == event_handler


@pytest.mark.asyncio
async def test_list_event_handlers(mocker, event_client, event_handler):
    mock = mocker.patch.object(EventResourceApiAdapter, "get_event_handlers")
    mock.return_value = [event_handler]
    result = await event_client.list_event_handlers()
    assert mock.called
    assert result == [event_handler]


@pytest.mark.asyncio
async def test_list_event_handlers_for_event(mocker, event_client, event_handler):
    mock = mocker.patch.object(EventResourceApiAdapter, "get_event_handlers_for_event")
    mock.return_value = [event_handler]
    result = await event_client.list_event_handlers_for_event(EVENT_NAME)
    mock.assert_called_with(event=EVENT_NAME)
    assert result == [event_handler]


@pytest.mark.asyncio
async def test_update_event_handler(mocker, event_client, event_handler):
    mock = mocker.patch.object(EventResourceApiAdapter, "update_event_handler")
    await event_client.update_event_handler(event_handler)
    mock.assert_called_with(event_handler=event_handler)


@pytest.mark.asyncio
async def test_delete_event_handler(mocker, event_client):
    mock = mocker.patch.object(EventResourceApiAdapter, "remove_event_handler_status")
    await event_client.delete_event_handler(HANDLER_NAME)
    mock.assert_called_with(name=HANDLER_NAME)


@pytest.mark.asyncio
async def test_get_event_handler_tags(mocker, event_client, tag_list):
    mock = mocker.patch.object(EventResourceApiAdapter, "get_tags_for_event_handler")
    mock.return_value = tag_list
    result = await event_client.get_event_handler_tags(HANDLER_NAME)
    mock.assert_called_with(name=HANDLER_NAME)
    assert result == tag_list


@pytest.mark.asyncio
async def test_add_event_handler_tag(mocker, event_client, tag_list):
    mock = mocker.patch.object(EventResourceApiAdapter, "put_tag_for_event_handler")
    await event_client.add_event_handler_tag(HANDLER_NAME, tag_list)
    mock.assert_called_with(name=HANDLER_NAME, tag=tag_list)


@pytest.mark.asyncio
async def test_remove_event_handler_tag(mocker, event_client, tag_list):
    mock = mocker.patch.object(EventResourceApiAdapter, "delete_tag_for_event_handler")
    await event_client.remove_event_handler_tag(HANDLER_NAME, tag_list)
    mock.assert_called_with(name=HANDLER_NAME, tag=tag_list)


@pytest.mark.asyncio
async def test_get_queue_configuration(mocker, event_client):
    mock = mocker.patch.object(EventResourceApiAdapter, "get_queue_config")
    config = {"bootstrapServers": "localhost:9092", "topic": "workflow_events"}
    mock.return_value = config
    result = await event_client.get_queue_configuration(QUEUE_TYPE, QUEUE_NAME)
    mock.assert_called_with(queue_type=QUEUE_TYPE, queue_name=QUEUE_NAME)
    assert result == config


@pytest.mark.asyncio
async def test_delete_queue_configuration(mocker, event_client):
    mock = mocker.patch.object(EventResourceApiAdapter, "delete_queue_config")
    await event_client.delete_queue_configuration(QUEUE_TYPE, QUEUE_NAME)
    mock.assert_called_with(queue_type=QUEUE_TYPE, queue_name=QUEUE_NAME)


@pytest.mark.asyncio
async def test_get_queue_names(mocker, event_client):
    mock = mocker.patch.object(EventResourceApiAdapter, "get_queue_names")
    queue_names = {"kafka": "workflow_events", "sqs": "task_events"}
    mock.return_value = queue_names
    result = await event_client.get_queue_names()
    assert mock.called
    assert result == queue_names


@pytest.mark.asyncio
async def test_handle_incoming_event(mocker, event_client):
    mock = mocker.patch.object(EventResourceApiAdapter, "handle_incoming_event")
    request_body = {"event": {"type": "workflow.completed", "data": {}}}
    await event_client.handle_incoming_event(request_body)
    mock.assert_called_with(request_body=request_body)


@pytest.mark.asyncio
async def test_put_queue_configuration(mocker, event_client):
    mock = mocker.patch.object(EventResourceApiAdapter, "put_queue_config")
    body = '{"bootstrapServers": "localhost:9092"}'
    await event_client.put_queue_configuration(QUEUE_TYPE, QUEUE_NAME, body)
    mock.assert_called_with(queue_type=QUEUE_TYPE, queue_name=QUEUE_NAME, body=body)


@pytest.mark.asyncio
async def test_test_method(mocker, event_client, event_handler):
    mock = mocker.patch.object(EventResourceApiAdapter, "test")
    mock.return_value = event_handler
    result = await event_client.test()
    assert mock.called
    assert result == event_handler


@pytest.mark.asyncio
async def test_test_connectivity(mocker, event_client):
    mock = mocker.patch.object(EventResourceApiAdapter, "test_connectivity")
    test_input = ConnectivityTestInputAdapter(
        connection_name="test_connection",
        sink="test_sink"
    )
    test_result = ConnectivityTestResultAdapter(
        success=True,
        message="Connection successful"
    )
    mock.return_value = test_result
    result = await event_client.test_connectivity(test_input)
    mock.assert_called_with(connectivity_test_input=test_input)
    assert result == test_result


@pytest.mark.asyncio
async def test_create_event_handler_multiple(mocker, event_client):
    mock = mocker.patch.object(EventResourceApiAdapter, "add_event_handler")
    handlers = [
        EventHandlerAdapter(name="handler1", event=EVENT_NAME, active=True),
        EventHandlerAdapter(name="handler2", event=EVENT_NAME, active=False),
    ]
    await event_client.create_event_handler(handlers)
    mock.assert_called_with(event_handler=handlers)


@pytest.mark.asyncio
async def test_list_event_handlers_empty(mocker, event_client):
    mock = mocker.patch.object(EventResourceApiAdapter, "get_event_handlers")
    mock.return_value = []
    result = await event_client.list_event_handlers()
    assert mock.called
    assert result == []


@pytest.mark.asyncio
async def test_list_event_handlers_for_event_empty(mocker, event_client):
    mock = mocker.patch.object(EventResourceApiAdapter, "get_event_handlers_for_event")
    mock.return_value = []
    result = await event_client.list_event_handlers_for_event(EVENT_NAME)
    mock.assert_called_with(event=EVENT_NAME)
    assert result == []


@pytest.mark.asyncio
async def test_add_event_handler_tag_empty_list(mocker, event_client):
    mock = mocker.patch.object(EventResourceApiAdapter, "put_tag_for_event_handler")
    await event_client.add_event_handler_tag(HANDLER_NAME, [])
    mock.assert_called_with(name=HANDLER_NAME, tag=[])


@pytest.mark.asyncio
async def test_remove_event_handler_tag_empty_list(mocker, event_client):
    mock = mocker.patch.object(EventResourceApiAdapter, "delete_tag_for_event_handler")
    await event_client.remove_event_handler_tag(HANDLER_NAME, [])
    mock.assert_called_with(name=HANDLER_NAME, tag=[])


@pytest.mark.asyncio
async def test_get_event_handler_tags_empty(mocker, event_client):
    mock = mocker.patch.object(EventResourceApiAdapter, "get_tags_for_event_handler")
    mock.return_value = []
    result = await event_client.get_event_handler_tags(HANDLER_NAME)
    mock.assert_called_with(name=HANDLER_NAME)
    assert result == []


@pytest.mark.asyncio
async def test_get_queue_names_empty(mocker, event_client):
    mock = mocker.patch.object(EventResourceApiAdapter, "get_queue_names")
    mock.return_value = {}
    result = await event_client.get_queue_names()
    assert mock.called
    assert result == {}
