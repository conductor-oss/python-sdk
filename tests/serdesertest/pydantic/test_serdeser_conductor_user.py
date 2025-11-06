import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.conductor_user_adapter import ConductorUserAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("ConductorUser")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_conductor_user_deserialization(raw_server_json, server_json):
    conductor_user_validation_error_adapter = ConductorUserAdapter.from_json(raw_server_json)
    assert conductor_user_validation_error_adapter.to_dict() == server_json


def test_conductor_user_serialization(raw_server_json, server_json):
    assert sorted(ConductorUserAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_conductor_user_validation_error():
    with pytest.raises(ValidationError):
        ConductorUserAdapter(groups="invalid group")
