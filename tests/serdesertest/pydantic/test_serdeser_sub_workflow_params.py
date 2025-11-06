
import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.sub_workflow_params_adapter import SubWorkflowParamsAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("SubWorkflowParams")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_sub_workflow_params_deserialization(raw_server_json, server_json):
    sub_workflow_params_adapter = SubWorkflowParamsAdapter.from_json(raw_server_json)
    assert sub_workflow_params_adapter.to_dict() == server_json


def test_sub_workflow_params_serialization(raw_server_json, server_json):
    assert sorted(SubWorkflowParamsAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_sub_workflow_params_invalid_data():
    with pytest.raises(ValidationError):
        SubWorkflowParamsAdapter(task_to_domain="invalid_task_to_domain")
