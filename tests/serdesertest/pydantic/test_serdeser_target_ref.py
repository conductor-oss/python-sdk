
import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.target_ref_adapter import TargetRefAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("TargetRef")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_target_ref_deserialization(raw_server_json, server_json):
    target_ref_adapter = TargetRefAdapter.from_json(raw_server_json)
    assert target_ref_adapter.to_dict() == server_json


def test_target_ref_serialization(raw_server_json, server_json):
    assert sorted(TargetRefAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_target_ref_invalid_data():
    with pytest.raises(ValidationError):
        TargetRefAdapter(id={"invalid_id"})
