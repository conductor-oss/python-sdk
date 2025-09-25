import json

import pytest

from conductor.client.http.models.integration_update import IntegrationUpdateAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("IntegrationUpdate"))


def test_integration_update_serdes(server_json):
    integration_update = IntegrationUpdateAdapter(
        category=server_json.get("category"),
        configuration=server_json.get("configuration"),
        description=server_json.get("description"),
        enabled=server_json.get("enabled"),
        type=server_json.get("type"),
    )
    assert server_json.get("category") == integration_update.category
    assert server_json.get("configuration") == integration_update.configuration
    assert server_json.get("description") == integration_update.description
    assert server_json.get("enabled") == integration_update.enabled
    assert server_json.get("type") == integration_update.type
    assert integration_update.category in [
        "API",
        "AI_MODEL",
        "VECTOR_DB",
        "RELATIONAL_DB",
    ]
    model_dict = integration_update.to_dict()
    assert server_json.get("category") == model_dict.get("category")
    assert server_json.get("configuration") == model_dict.get("configuration")
    assert server_json.get("description") == model_dict.get("description")
    assert server_json.get("enabled") == model_dict.get("enabled")
    assert server_json.get("type") == model_dict.get("type")
    if integration_update.configuration:
        assert server_json.get("configuration") == model_dict.get("configuration")
