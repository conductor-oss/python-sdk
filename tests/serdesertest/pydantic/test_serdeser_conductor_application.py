import json

import pytest

from conductor.asyncio_client.adapters.models.extended_conductor_application_adapter import ExtendedConductorApplicationAdapter
from conductor.client.http.models import ConductorApplication
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("ConductorApplication"))


def test_serialization_deserialization(server_json):
    conductor_app = ConductorApplication(
        id=server_json.get("id"),
        name=server_json.get("name"),
        created_by=server_json.get("createdBy"),
    )
    assert conductor_app.id == server_json.get("id")
    assert conductor_app.name == server_json.get("name")
    assert conductor_app.created_by == server_json.get("createdBy")
    serialized_json = conductor_app.to_dict()
    assert serialized_json.get("id") == server_json.get("id")
    assert serialized_json.get("name") == server_json.get("name")
    assert serialized_json.get("created_by") == server_json.get("createdBy")
