import json

import pytest

from conductor.asyncio_client.adapters.models.poll_data_adapter import PollDataAdapter
from conductor.client.http.models.poll_data import PollData
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("PollData")
    return json.loads(server_json_str)


def test_poll_data_serdes(server_json):
    # 1. Test deserialization from JSON to PollData object
    poll_data = PollData(
        queue_name=server_json.get("queueName"),
        domain=server_json.get("domain"),
        worker_id=server_json.get("workerId"),
        last_poll_time=server_json.get("lastPollTime"),
    )

    # 2. Verify all fields are correctly populated
    assert poll_data.queue_name == server_json.get("queueName")
    assert poll_data.domain == server_json.get("domain")
    assert poll_data.worker_id == server_json.get("workerId")
    assert poll_data.last_poll_time == server_json.get("lastPollTime")

    # 3. Test serialization back to JSON
    serialized_json = poll_data.to_dict()

    # Convert to server JSON format (camelCase)
    result_json = {
        "queueName": serialized_json.get("queue_name"),
        "domain": serialized_json.get("domain"),
        "workerId": serialized_json.get("worker_id"),
        "lastPollTime": serialized_json.get("last_poll_time"),
    }

    # 4. Verify resulting JSON matches the original
    assert result_json.get("queueName") == server_json.get("queueName")
    assert result_json.get("domain") == server_json.get("domain")
    assert result_json.get("workerId") == server_json.get("workerId")
    assert result_json.get("lastPollTime") == server_json.get("lastPollTime")

    # Additional verifications
    # Ensure no data loss by comparing keys
    assert set(result_json.keys()) == set(server_json.keys())
