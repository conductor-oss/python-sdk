import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.create_or_update_application_request_adapter import CreateOrUpdateApplicationRequestAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("CreateOrUpdateApplicationRequest")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_create_or_update_application_ids_deserialization(raw_server_json, server_json):
    create_or_update_application_ids_adapter = CreateOrUpdateApplicationRequestAdapter.from_json(raw_server_json)
    assert create_or_update_application_ids_adapter.to_dict() == server_json


def test_create_or_update_application_ids_serialization(raw_server_json, server_json):
    assert sorted(CreateOrUpdateApplicationRequestAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_create_or_update_application_ids_validation_error():
    with pytest.raises(ValidationError):
        CreateOrUpdateApplicationRequestAdapter(name=1)
