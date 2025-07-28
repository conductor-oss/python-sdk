import json

import pytest

from conductor.client.http.models.integration_api import IntegrationApi
from conductor.client.http.models.tag_object import TagObject
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("IntegrationApi"))


def test_integration_api_serialization_deserialization(server_json):
    integration_api = IntegrationApi(
        api=server_json.get("api"),
        configuration=server_json.get("configuration"),
        created_by=server_json.get("createdBy"),
        created_on=server_json.get("createdOn"),
        description=server_json.get("description"),
        enabled=server_json.get("enabled"),
        integration_name=server_json.get("integrationName"),
        tags=(
            [
                TagObject(key=tag.get("key"), value=tag.get("value"))
                for tag in server_json.get("tags", [])
            ]
            if server_json.get("tags")
            else None
        ),
        updated_by=server_json.get("updatedBy"),
        updated_on=server_json.get("updatedOn"),
    )
    assert server_json.get("api") == integration_api.api
    assert server_json.get("description") == integration_api.description
    assert server_json.get("enabled") == integration_api.enabled
    assert server_json.get("integrationName") == integration_api.integration_name
    assert server_json.get("createdBy") == integration_api.created_by
    assert server_json.get("createdOn") == integration_api.created_on
    assert server_json.get("updatedBy") == integration_api.updated_by
    assert server_json.get("updatedOn") == integration_api.updated_on
    assert server_json.get("configuration") == integration_api.configuration
    if server_json.get("tags"):
        assert len(server_json.get("tags")) == len(integration_api.tags)
        for i, tag in enumerate(integration_api.tags):
            assert isinstance(tag, TagObject)
            assert server_json.get("tags")[i].get("key") == tag.key
            assert server_json.get("tags")[i].get("value") == tag.value
    serialized_json = integration_api.to_dict()
    for field in ["api", "description", "enabled"]:
        json_field = field
        if field in IntegrationApi.attribute_map:
            json_field = IntegrationApi.attribute_map[field]
        assert server_json.get(json_field) == serialized_json.get(field)
    assert server_json.get("createdBy") == serialized_json.get("created_by")
    assert server_json.get("createdOn") == serialized_json.get("created_on")
    assert server_json.get("updatedBy") == serialized_json.get("updated_by")
    assert server_json.get("updatedOn") == serialized_json.get("updated_on")
    assert server_json.get("integrationName") == serialized_json.get("integration_name")
    assert server_json.get("configuration") == serialized_json.get("configuration")
    if server_json.get("tags"):
        for i, original_tag in enumerate(server_json.get("tags")):
            serialized_tag = serialized_json.get("tags")[i]
            assert original_tag.get("key") == serialized_tag.get("key")
            assert original_tag.get("value") == serialized_tag.get("value")
