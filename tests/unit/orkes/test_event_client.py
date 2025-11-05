import logging
import pytest

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.event_resource_api import EventResourceApi
from conductor.client.adapters.models.event_handler_adapter import EventHandlerAdapter
from conductor.client.adapters.models.tag_adapter import TagAdapter
from conductor.client.http.models.connectivity_test_input import ConnectivityTestInput
from conductor.client.http.models.connectivity_test_result import ConnectivityTestResult
from conductor.client.orkes.orkes_event_client import OrkesEventClient

EVENT_NAME = "workflow:completed"
HANDLER_NAME = "test_handler"
QUEUE_TYPE = "kafka"
QUEUE_NAME = "test_queue"


@pytest.fixture(scope="module")
def event_client():
    configuration = Configuration("http://localhost:8080/api")
    return OrkesEventClient(configuration)


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
    message = "event_api is not of type EventResourceApi"
    assert isinstance(event_client._event_api, EventResourceApi), message


def test_create_event_handler(mocker, event_client, event_handler):
    mock = mocker.patch.object(EventResourceApi, "add_event_handler")
    event_client.create_event_handler([event_handler])
    mock.assert_called_with([event_handler])


def test_get_event_handler(mocker, event_client, event_handler):
    mock = mocker.patch.object(EventResourceApi, "get_event_handler_by_name")
    mock.return_value = event_handler
    result = event_client.get_event_handler(HANDLER_NAME)
    mock.assert_called_with(name=HANDLER_NAME)
    assert result == event_handler


def test_list_event_handlers(mocker, event_client, event_handler):
    mock = mocker.patch.object(EventResourceApi, "get_event_handlers")
    mock.return_value = [event_handler]
    result = event_client.list_event_handlers()
    assert mock.called
    assert result == [event_handler]


def test_list_event_handlers_for_event(mocker, event_client, event_handler):
    mock = mocker.patch.object(EventResourceApi, "get_event_handlers_for_event")
    mock.return_value = [event_handler]
    result = event_client.list_event_handlers_for_event(EVENT_NAME)
    mock.assert_called_with(event=EVENT_NAME)
    assert result == [event_handler]


def test_update_event_handler(mocker, event_client, event_handler):
    mock = mocker.patch.object(EventResourceApi, "update_event_handler")
    event_client.update_event_handler(event_handler)
    mock.assert_called_with(event_handler)


def test_delete_event_handler(mocker, event_client):
    mock = mocker.patch.object(EventResourceApi, "remove_event_handler_status")
    event_client.delete_event_handler(HANDLER_NAME)
    mock.assert_called_with(name=HANDLER_NAME)


def test_get_event_handler_tags(mocker, event_client, tag_list):
    mock = mocker.patch.object(EventResourceApi, "get_tags_for_event_handler")
    mock.return_value = tag_list
    result = event_client.get_event_handler_tags(HANDLER_NAME)
    mock.assert_called_with(name=HANDLER_NAME)
    assert result == tag_list


def test_add_event_handler_tag(mocker, event_client, tag_list):
    mock = mocker.patch.object(EventResourceApi, "put_tag_for_event_handler")
    event_client.add_event_handler_tag(HANDLER_NAME, tag_list)
    mock.assert_called_with(tag_list, HANDLER_NAME)


def test_remove_event_handler_tag(mocker, event_client, tag_list):
    mock = mocker.patch.object(EventResourceApi, "delete_tag_for_event_handler")
    event_client.remove_event_handler_tag(HANDLER_NAME, tag_list)
    mock.assert_called_with(tag_list, HANDLER_NAME)


def test_get_queue_configuration(mocker, event_client):
    mock = mocker.patch.object(EventResourceApi, "get_queue_config")
    config = {"bootstrapServers": "localhost:9092", "topic": "workflow_events"}
    mock.return_value = config
    result = event_client.get_queue_configuration(QUEUE_TYPE, QUEUE_NAME)
    mock.assert_called_with(queue_type=QUEUE_TYPE, queue_name=QUEUE_NAME)
    assert result == config


def test_delete_queue_configuration(mocker, event_client):
    mock = mocker.patch.object(EventResourceApi, "delete_queue_config")
    event_client.delete_queue_configuration(QUEUE_TYPE, QUEUE_NAME)
    mock.assert_called_with(queue_type=QUEUE_TYPE, queue_name=QUEUE_NAME)


def test_get_queue_names(mocker, event_client):
    mock = mocker.patch.object(EventResourceApi, "get_queue_names")
    queue_names = {"kafka": "workflow_events", "sqs": "task_events"}
    mock.return_value = queue_names
    result = event_client.get_queue_names()
    assert mock.called
    assert result == queue_names


def test_handle_incoming_event(mocker, event_client):
    mock = mocker.patch.object(EventResourceApi, "handle_incoming_event")
    request_body = {"event": {"type": "workflow.completed", "data": {}}}
    event_client.handle_incoming_event(request_body)
    mock.assert_called_with(request_body)


def test_put_queue_config(mocker, event_client):
    mock = mocker.patch.object(EventResourceApi, "put_queue_config")
    body = '{"bootstrapServers": "localhost:9092"}'
    event_client.put_queue_config(body, QUEUE_TYPE, QUEUE_NAME)
    mock.assert_called_with(body, QUEUE_TYPE, QUEUE_NAME)


def test_test_method(mocker, event_client):
    from conductor.client.http.models.event_handler import EventHandler
    mock = mocker.patch.object(EventResourceApi, "test")
    event_handler = EventHandler()
    mock.return_value = event_handler
    result = event_client.test()
    assert mock.called
    assert result == event_handler


def test_test_connectivity(mocker, event_client):
    mock = mocker.patch.object(EventResourceApi, "test_connectivity")
    test_input = ConnectivityTestInput(
        input="test_connection",
        sink="test_sink"
    )
    test_result = ConnectivityTestResult(
        successful=True,
        reason="Connection successful"
    )
    mock.return_value = test_result
    result = event_client.test_connectivity(test_input)
    mock.assert_called_with(test_input)
    assert result == test_result


def test_create_event_handler_multiple(mocker, event_client):
    mock = mocker.patch.object(EventResourceApi, "add_event_handler")
    handlers = [
        EventHandlerAdapter(name="handler1", event=EVENT_NAME, active=True),
        EventHandlerAdapter(name="handler2", event=EVENT_NAME, active=False),
    ]
    event_client.create_event_handler(handlers)
    mock.assert_called_with(handlers)


def test_list_event_handlers_empty(mocker, event_client):
    mock = mocker.patch.object(EventResourceApi, "get_event_handlers")
    mock.return_value = []
    result = event_client.list_event_handlers()
    assert mock.called
    assert result == []


def test_list_event_handlers_for_event_empty(mocker, event_client):
    mock = mocker.patch.object(EventResourceApi, "get_event_handlers_for_event")
    mock.return_value = []
    result = event_client.list_event_handlers_for_event(EVENT_NAME)
    mock.assert_called_with(event=EVENT_NAME)
    assert result == []


def test_add_event_handler_tag_empty_list(mocker, event_client):
    mock = mocker.patch.object(EventResourceApi, "put_tag_for_event_handler")
    event_client.add_event_handler_tag(HANDLER_NAME, [])
    mock.assert_called_with([], HANDLER_NAME)


def test_remove_event_handler_tag_empty_list(mocker, event_client):
    mock = mocker.patch.object(EventResourceApi, "delete_tag_for_event_handler")
    event_client.remove_event_handler_tag(HANDLER_NAME, [])
    mock.assert_called_with([], HANDLER_NAME)


def test_get_event_handler_tags_empty(mocker, event_client):
    mock = mocker.patch.object(EventResourceApi, "get_tags_for_event_handler")
    mock.return_value = []
    result = event_client.get_event_handler_tags(HANDLER_NAME)
    mock.assert_called_with(name=HANDLER_NAME)
    assert result == []


def test_get_queue_names_empty(mocker, event_client):
    mock = mocker.patch.object(EventResourceApi, "get_queue_names")
    mock.return_value = {}
    result = event_client.get_queue_names()
    assert mock.called
    assert result == {}
