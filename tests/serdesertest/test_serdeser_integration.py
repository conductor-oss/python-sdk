import json

import pytest

from conductor.client.adapters.models.integration_adapter import IntegrationAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("Integration"))


def test_integration_serdeser(server_json):
    integration = IntegrationAdapter(
        category=server_json.get("category"),
        configuration=server_json.get("configuration"),
        created_by=server_json.get("createdBy"),
        created_on=server_json.get("createdOn"),
        description=server_json.get("description"),
        enabled=server_json.get("enabled"),
        models_count=server_json.get("modelsCount"),
        name=server_json.get("name"),
        tags=server_json.get("tags"),
        type=server_json.get("type"),
        updated_by=server_json.get("updatedBy"),
        updated_on=server_json.get("updatedOn"),
        apis=server_json.get("apis"),
    )
    assert server_json.get("category") == integration.category
    assert server_json.get("configuration") == integration.configuration
    assert server_json.get("createdBy") == integration.created_by
    assert server_json.get("createdOn") == integration.created_on
    assert server_json.get("description") == integration.description
    assert server_json.get("enabled") == integration.enabled
    assert server_json.get("modelsCount") == integration.models_count
    assert server_json.get("name") == integration.name
    assert server_json.get("tags") == integration.tags
    assert server_json.get("type") == integration.type
    assert server_json.get("updatedBy") == integration.updated_by
    assert server_json.get("updatedOn") == integration.updated_on
    assert server_json.get("apis") == integration.apis
    if integration.category is not None:
        assert integration.category in ["API", "AI_MODEL", "VECTOR_DB", "RELATIONAL_DB"]
    serialized_dict = integration.to_dict()
    transformed_dict = {}
    for snake_key, value in serialized_dict.items():
        camel_key = integration.attribute_map.get(snake_key, snake_key)
        transformed_dict[camel_key] = value
    for key, value in server_json.items():
        assert value == transformed_dict.get(key)
