import json

import pytest

from conductor.client.http.models.generate_token_request import GenerateTokenRequestAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("GenerateTokenRequest"))


def test_generate_token_request_ser_des(server_json):
    model_obj = GenerateTokenRequestAdapter(
        key_id=server_json["keyId"], key_secret=server_json["keySecret"]
    )
    assert model_obj.key_id == server_json["keyId"]
    assert model_obj.key_secret == server_json["keySecret"]
    model_json = model_obj.to_dict()
    serialized_json = {
        "keyId": model_json["key_id"],
        "keySecret": model_json["key_secret"],
    }
    assert serialized_json["keyId"] == server_json["keyId"]
    assert serialized_json["keySecret"] == server_json["keySecret"]
    duplicate_obj = GenerateTokenRequestAdapter(
        key_id=server_json["keyId"], key_secret=server_json["keySecret"]
    )
    assert model_obj == duplicate_obj
    assert model_obj != GenerateTokenRequestAdapter(key_id="different", key_secret="values")
