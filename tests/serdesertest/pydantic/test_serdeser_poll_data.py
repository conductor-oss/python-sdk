
import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.poll_data_adapter import PollDataAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("PollData")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_poll_data_deserialization(raw_server_json, server_json):
    poll_data_adapter = PollDataAdapter.from_json(raw_server_json)
    assert poll_data_adapter.to_dict() == server_json


def test_poll_data_serialization(raw_server_json, server_json):
    assert sorted(PollDataAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_poll_data_invalid_data():
    with pytest.raises(ValidationError):
        PollDataAdapter(domain={"invalid_domain"})
