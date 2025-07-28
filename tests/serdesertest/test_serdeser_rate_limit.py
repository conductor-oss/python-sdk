import json
import re

import pytest

from conductor.client.http.models.rate_limit import RateLimit
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("RateLimitConfig"))


def camel_to_snake(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def test_serialization_deserialization(server_json):
    rate_limit = RateLimit(
        rate_limit_key=server_json.get("rateLimitKey"),
        concurrent_exec_limit=server_json.get("concurrentExecLimit"),
        tag=server_json.get("tag"),
        concurrent_execution_limit=server_json.get("concurrentExecutionLimit"),
    )
    assert server_json.get("rateLimitKey") == rate_limit.rate_limit_key
    assert server_json.get("concurrentExecLimit") == rate_limit.concurrent_exec_limit
    assert server_json.get("tag") == rate_limit.tag
    assert (
        server_json.get("concurrentExecutionLimit")
        == rate_limit.concurrent_execution_limit
    )
    model_dict = rate_limit.to_dict()
    for key, value in server_json.items():
        snake_key = camel_to_snake(key)
        assert snake_key in model_dict
        assert value == model_dict[snake_key]
