import json

import pytest

from conductor.client.adapters.models.tag_adapter import TagAdapter, TypeEnum
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("Tag")
    return json.loads(server_json_str)


def test_tag_string_serde(server_json):
    """Test serialization and deserialization of TagString model"""
    # 1. Deserialize JSON into model object
    tag_string = TagAdapter(
        key=server_json.get("key"),
        type=server_json.get("type"),
        value=server_json.get("value"),
    )
    # 2. Verify all fields are properly populated
    assert server_json.get("key") == tag_string.key
    assert server_json.get("type") == tag_string.type
    assert server_json.get("value") == tag_string.value
    # Specific enum validation if 'type' is present
    if server_json.get("type"):
        assert tag_string.type in [TypeEnum.METADATA.value, TypeEnum.RATE_LIMIT.value]
    # 3. Serialize model back to JSON
    model_dict = tag_string.to_dict()
    model_json = json.dumps(model_dict)
    model_dict_reloaded = json.loads(model_json)
    # 4. Verify JSON matches the original
    # Note: Only compare fields that were in the original JSON
    for key in server_json:
        assert server_json[key] == model_dict_reloaded[key]
    # Create another instance using the dict and verify equality
    reconstructed_tag = TagAdapter(
        key=model_dict_reloaded.get("key"),
        type=model_dict_reloaded.get("type"),
        value=model_dict_reloaded.get("value"),
    )
    assert tag_string == reconstructed_tag
