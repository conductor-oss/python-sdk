import json

import pytest

from conductor.client.http.models.correlation_ids_search_request import CorrelationIdsSearchRequestAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(
        JsonTemplateResolver.get_json_string("CorrelationIdsSearchRequest")
    )


def test_serdeser_correlation_ids_search_request(server_json):
    python_format_json = {}
    for key, value in server_json.items():
        python_key = next(
            (
                k
                for k, v in CorrelationIdsSearchRequestAdapter.attribute_map.items()
                if v == key
            ),
            key,
        )
        python_format_json[python_key] = value
    model_obj = CorrelationIdsSearchRequestAdapter(**python_format_json)
    assert model_obj.correlation_ids is not None
    assert isinstance(model_obj.correlation_ids, list)
    for item in model_obj.correlation_ids:
        assert isinstance(item, str)
    assert model_obj.workflow_names is not None
    assert isinstance(model_obj.workflow_names, list)
    for item in model_obj.workflow_names:
        assert isinstance(item, str)
    serialized_dict = model_obj.to_dict()
    json_dict = {}
    for attr, value in serialized_dict.items():
        if attr in model_obj.attribute_map:
            json_dict[model_obj.attribute_map[attr]] = value
        else:
            json_dict[attr] = value
    assert server_json == json_dict
