import json

import pytest

from conductor.client.adapters.models.external_storage_location_adapter import ExternalStorageLocationAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("ExternalStorageLocation"))


def test_external_storage_location_serde(server_json):
    model = ExternalStorageLocationAdapter(
        uri=server_json.get("uri"), path=server_json.get("path")
    )
    assert server_json.get("uri") == model.uri
    assert server_json.get("path") == model.path
    model_dict = model.to_dict()
    assert server_json.get("uri") == model_dict.get("uri")
    assert server_json.get("path") == model_dict.get("path")
    assert set(server_json.keys()) == set(model_dict.keys())
