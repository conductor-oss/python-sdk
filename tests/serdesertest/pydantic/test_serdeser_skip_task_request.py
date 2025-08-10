import json

import pytest

from conductor.asyncio_client.adapters.models.skip_task_request_adapter import SkipTaskRequestAdapter
from conductor.client.http.models.skip_task_request import SkipTaskRequest
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("SkipTaskRequest")
    return json.loads(server_json_str)


def test_skip_task_request_serde(server_json):
    # 1. Deserialize server JSON to model using constructor
    model = SkipTaskRequest(
        task_input=server_json.get("taskInput"),
        task_output=server_json.get("taskOutput"),
    )
    # 2. Verify all fields populated correctly
    assert server_json.get("taskInput") == model.task_input
    assert server_json.get("taskOutput") == model.task_output
    # Verify nested structures if they exist
    if isinstance(model.task_input, dict):
        for key, value in server_json.get("taskInput").items():
            assert value == model.task_input.get(key)
    if isinstance(model.task_output, dict):
        for key, value in server_json.get("taskOutput").items():
            assert value == model.task_output.get(key)
    # 3. Create a dict manually matching the server format
    json_from_model = {
        "taskInput": model.task_input,
        "taskOutput": model.task_output,
    }
    # Remove None values
    json_from_model = {k: v for k, v in json_from_model.items() if v is not None}
    # 4. Compare with original JSON
    assert server_json == json_from_model
