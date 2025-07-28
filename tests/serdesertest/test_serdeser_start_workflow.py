import json

import pytest

from conductor.client.http.models.start_workflow import StartWorkflow
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(
        JsonTemplateResolver.get_json_string("EventHandler.StartWorkflow")
    )


def test_serdes_start_workflow(server_json):
    model = StartWorkflow(
        name=server_json.get("name"),
        version=server_json.get("version"),
        correlation_id=server_json.get("correlationId"),
        input=server_json.get("input"),
        task_to_domain=server_json.get("taskToDomain"),
    )
    assert server_json.get("name") == model.name
    assert server_json.get("version") == model.version
    assert server_json.get("correlationId") == model.correlation_id
    if "input" in server_json:
        assert model.input is not None
        assert server_json.get("input") == model.input
        if isinstance(model.input, dict) and len(model.input) > 0:
            first_key = next(iter(model.input))
            assert first_key is not None
    if "taskToDomain" in server_json:
        assert model.task_to_domain is not None
        assert server_json.get("taskToDomain") == model.task_to_domain
        if isinstance(model.task_to_domain, dict) and len(model.task_to_domain) > 0:
            first_key = next(iter(model.task_to_domain))
            assert first_key is not None
            assert isinstance(model.task_to_domain[first_key], str)
    model_dict = model.to_dict()
    assert server_json.get("name") == model_dict.get("name")
    assert server_json.get("version") == model_dict.get("version")
    assert server_json.get("correlationId") == model_dict.get("correlation_id")
    assert server_json.get("input") == model_dict.get("input")
    assert server_json.get("taskToDomain") == model_dict.get("task_to_domain")
