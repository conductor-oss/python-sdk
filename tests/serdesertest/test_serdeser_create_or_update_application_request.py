import json

import pytest

from conductor.client.adapters.models.create_or_update_application_request_adapter import CreateOrUpdateApplicationRequestAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(
        JsonTemplateResolver.get_json_string("CreateOrUpdateApplicationRequest")
    )


def test_deserialize_serialize(server_json):
    model = CreateOrUpdateApplicationRequestAdapter()
    model_dict = server_json
    if "name" in model_dict:
        model.name = model_dict["name"]
    expected_name = server_json.get("name")
    assert model.name == expected_name
    serialized_dict = model.to_dict()
    assert serialized_dict.get("name") == server_json.get("name")
    assert serialized_dict == server_json
