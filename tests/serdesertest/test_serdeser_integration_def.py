import json

import pytest

from conductor.client.http.models.integration_def import IntegrationDefAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("IntegrationDef"))


def test_serialization_deserialization(server_json):
    integration_def = IntegrationDefAdapter(
        category=server_json["category"],
        category_label=server_json["categoryLabel"],
        configuration=server_json["configuration"],
        description=server_json["description"],
        enabled=server_json["enabled"],
        icon_name=server_json["iconName"],
        name=server_json["name"],
        tags=server_json["tags"],
        type=server_json["type"],
    )
    assert integration_def.category == server_json["category"]
    assert integration_def.category_label == server_json["categoryLabel"]
    assert integration_def.configuration == server_json["configuration"]
    assert integration_def.description == server_json["description"]
    assert integration_def.enabled == server_json["enabled"]
    assert integration_def.icon_name == server_json["iconName"]
    assert integration_def.name == server_json["name"]
    assert integration_def.tags == server_json["tags"]
    assert integration_def.type == server_json["type"]
    assert integration_def.category in ["API", "AI_MODEL", "VECTOR_DB", "RELATIONAL_DB"]
    if integration_def.tags:
        assert isinstance(integration_def.tags, list)
    if integration_def.configuration:
        assert isinstance(integration_def.configuration, list)
    serialized_json = integration_def.to_dict()
    assert serialized_json["category"] == server_json["category"]
    assert serialized_json["category_label"] == server_json["categoryLabel"]
    assert serialized_json["configuration"] == server_json["configuration"]
    assert serialized_json["description"] == server_json["description"]
    assert serialized_json["enabled"] == server_json["enabled"]
    assert serialized_json["icon_name"] == server_json["iconName"]
    assert serialized_json["name"] == server_json["name"]
    assert serialized_json["tags"] == server_json["tags"]
    assert serialized_json["type"] == server_json["type"]
