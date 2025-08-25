import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.rate_limit_config_adapter import RateLimitConfigAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("RateLimitConfig")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_rate_limit_config_deserialization(raw_server_json, server_json):
    rate_limit_config_adapter = RateLimitConfigAdapter.from_json(raw_server_json)
    assert rate_limit_config_adapter.to_dict() == server_json


def test_rate_limit_config_serialization(raw_server_json, server_json):
    assert sorted(RateLimitConfigAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_rate_limit_config_invalid_data():
    with pytest.raises(ValidationError):
        RateLimitConfigAdapter(rate_limit_key={"invalid_key"})
