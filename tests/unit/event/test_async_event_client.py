import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from conductor.asyncio_client.event.event_client import AsyncEventClient
from conductor.asyncio_client.adapters import ApiClient
from conductor.shared.event.configuration import QueueConfiguration
from conductor.shared.event.configuration.kafka_queue import KafkaQueueConfiguration, KafkaConsumerConfiguration, KafkaProducerConfiguration


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def mock_api_client():
    return MagicMock(spec=ApiClient)


@pytest.fixture
def mock_event_resource_api():
    return AsyncMock()


@pytest.fixture
def event_client(mock_api_client, mock_event_resource_api):
    with patch('conductor.asyncio_client.event.event_client.EventResourceApiAdapter', return_value=mock_event_resource_api):
        client = AsyncEventClient(mock_api_client)
        client.client = mock_event_resource_api
        return client


@pytest.fixture
def kafka_queue_config():
    config = KafkaQueueConfiguration("test_topic")
    consumer_config = KafkaConsumerConfiguration("localhost:9092")
    producer_config = KafkaProducerConfiguration("localhost:9092")
    config.add_consumer(consumer_config)
    config.add_producer(producer_config)
    return config


@pytest.mark.asyncio
async def test_delete_queue_configuration_success(event_client, kafka_queue_config, mock_event_resource_api):
    await event_client.delete_queue_configuration(kafka_queue_config)
    
    mock_event_resource_api.delete_queue_config.assert_called_once_with(
        queue_name="test_topic",
        queue_type="kafka"
    )


@pytest.mark.asyncio
async def test_get_kafka_queue_configuration_success(event_client, mock_event_resource_api):
    expected_config = KafkaQueueConfiguration("test_topic")
    mock_event_resource_api.get_queue_config.return_value = expected_config
    
    result = await event_client.get_kafka_queue_configuration("test_topic")
    
    mock_event_resource_api.get_queue_config.assert_called_once_with("kafka", "test_topic")
    assert result == expected_config


@pytest.mark.asyncio
async def test_get_queue_configuration_success(event_client, mock_event_resource_api):
    expected_config = MagicMock()
    mock_event_resource_api.get_queue_config.return_value = expected_config
    
    result = await event_client.get_queue_configuration("kafka", "test_topic")
    
    mock_event_resource_api.get_queue_config.assert_called_once_with("kafka", "test_topic")
    assert result == expected_config


@pytest.mark.asyncio
async def test_put_queue_configuration_success(event_client, kafka_queue_config, mock_event_resource_api):
    await event_client.put_queue_configuration(kafka_queue_config)
    
    mock_event_resource_api.put_queue_config.assert_called_once_with(
        body=kafka_queue_config.get_worker_configuration(),
        queue_name="test_topic",
        queue_type="kafka"
    )


@pytest.mark.asyncio
async def test_delete_queue_configuration_error_handling(event_client, kafka_queue_config, mock_event_resource_api):
    mock_event_resource_api.delete_queue_config.side_effect = Exception("Delete failed")
    
    with pytest.raises(Exception, match="Delete failed"):
        await event_client.delete_queue_configuration(kafka_queue_config)


@pytest.mark.asyncio
async def test_get_kafka_queue_configuration_error_handling(event_client, mock_event_resource_api):
    mock_event_resource_api.get_queue_config.side_effect = Exception("Get failed")
    
    with pytest.raises(Exception, match="Get failed"):
        await event_client.get_kafka_queue_configuration("test_topic")


@pytest.mark.asyncio
async def test_get_queue_configuration_error_handling(event_client, mock_event_resource_api):
    mock_event_resource_api.get_queue_config.side_effect = Exception("Get failed")
    
    with pytest.raises(Exception, match="Get failed"):
        await event_client.get_queue_configuration("kafka", "test_topic")


@pytest.mark.asyncio
async def test_put_queue_configuration_error_handling(event_client, kafka_queue_config, mock_event_resource_api):
    mock_event_resource_api.put_queue_config.side_effect = Exception("Put failed")
    
    with pytest.raises(Exception, match="Put failed"):
        await event_client.put_queue_configuration(kafka_queue_config)


@pytest.mark.asyncio
async def test_get_kafka_queue_configuration_calls_get_queue_configuration(event_client, mock_event_resource_api):
    expected_config = MagicMock()
    mock_event_resource_api.get_queue_config.return_value = expected_config
    
    result = await event_client.get_kafka_queue_configuration("test_topic")
    
    mock_event_resource_api.get_queue_config.assert_called_once_with("kafka", "test_topic")
    assert result == expected_config


@pytest.mark.asyncio
async def test_delete_queue_configuration_with_different_queue_types(event_client, mock_event_resource_api):
    config = MagicMock(spec=QueueConfiguration)
    config.queue_name = "test_queue"
    config.queue_type = "redis"
    
    await event_client.delete_queue_configuration(config)
    
    mock_event_resource_api.delete_queue_config.assert_called_once_with(
        queue_name="test_queue",
        queue_type="redis"
    )


@pytest.mark.asyncio
async def test_put_queue_configuration_with_different_queue_types(event_client, mock_event_resource_api):
    config = MagicMock(spec=QueueConfiguration)
    config.queue_name = "test_queue"
    config.queue_type = "redis"
    config.get_worker_configuration.return_value = {"test": "config"}
    
    await event_client.put_queue_configuration(config)
    
    mock_event_resource_api.put_queue_config.assert_called_once_with(
        body={"test": "config"},
        queue_name="test_queue",
        queue_type="redis"
    )


@pytest.mark.asyncio
async def test_get_queue_configuration_with_different_queue_types(event_client, mock_event_resource_api):
    expected_config = MagicMock()
    mock_event_resource_api.get_queue_config.return_value = expected_config
    
    result = await event_client.get_queue_configuration("redis", "test_queue")
    
    mock_event_resource_api.get_queue_config.assert_called_once_with("redis", "test_queue")
    assert result == expected_config


@pytest.mark.asyncio
async def test_delete_queue_configuration_returns_none(event_client, kafka_queue_config, mock_event_resource_api):
    mock_event_resource_api.delete_queue_config.return_value = None
    
    result = await event_client.delete_queue_configuration(kafka_queue_config)
    
    assert result is None


@pytest.mark.asyncio
async def test_put_queue_configuration_returns_result(event_client, kafka_queue_config, mock_event_resource_api):
    expected_result = MagicMock()
    mock_event_resource_api.put_queue_config.return_value = expected_result
    
    result = await event_client.put_queue_configuration(kafka_queue_config)
    
    assert result == expected_result


@pytest.mark.asyncio
async def test_get_queue_configuration_returns_config(event_client, mock_event_resource_api):
    expected_config = MagicMock()
    mock_event_resource_api.get_queue_config.return_value = expected_config
    
    result = await event_client.get_queue_configuration("kafka", "test_topic")
    
    assert result == expected_config


@pytest.mark.asyncio
async def test_get_kafka_queue_configuration_returns_config(event_client, mock_event_resource_api):
    expected_config = MagicMock()
    mock_event_resource_api.get_queue_config.return_value = expected_config
    
    result = await event_client.get_kafka_queue_configuration("test_topic")
    
    assert result == expected_config


@pytest.mark.asyncio
async def test_delete_queue_configuration_with_empty_queue_name(event_client, mock_event_resource_api):
    config = MagicMock(spec=QueueConfiguration)
    config.queue_name = ""
    config.queue_type = "kafka"
    
    await event_client.delete_queue_configuration(config)
    
    mock_event_resource_api.delete_queue_config.assert_called_once_with(
        queue_name="",
        queue_type="kafka"
    )


@pytest.mark.asyncio
async def test_put_queue_configuration_with_empty_queue_name(event_client, mock_event_resource_api):
    config = MagicMock(spec=QueueConfiguration)
    config.queue_name = ""
    config.queue_type = "kafka"
    config.get_worker_configuration.return_value = {}
    
    await event_client.put_queue_configuration(config)
    
    mock_event_resource_api.put_queue_config.assert_called_once_with(
        body={},
        queue_name="",
        queue_type="kafka"
    )


@pytest.mark.asyncio
async def test_get_queue_configuration_with_empty_queue_name(event_client, mock_event_resource_api):
    expected_config = MagicMock()
    mock_event_resource_api.get_queue_config.return_value = expected_config
    
    result = await event_client.get_queue_configuration("kafka", "")
    
    mock_event_resource_api.get_queue_config.assert_called_once_with("kafka", "")
    assert result == expected_config


@pytest.mark.asyncio
async def test_get_kafka_queue_configuration_with_empty_topic(event_client, mock_event_resource_api):
    expected_config = MagicMock()
    mock_event_resource_api.get_queue_config.return_value = expected_config
    
    result = await event_client.get_kafka_queue_configuration("")
    
    mock_event_resource_api.get_queue_config.assert_called_once_with("kafka", "")
    assert result == expected_config 