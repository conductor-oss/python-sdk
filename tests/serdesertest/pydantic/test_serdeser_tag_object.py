
import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("Tag")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_tag_object_deserialization(raw_server_json, server_json):
    tag_object_adapter = TagAdapter.from_json(raw_server_json)
    assert tag_object_adapter.to_dict() == server_json


def test_tag_object_serialization(raw_server_json, server_json):
    assert sorted(TagAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_tag_object_invalid_data():
    with pytest.raises(ValidationError):
        TagAdapter(key={"invalid_key"})
