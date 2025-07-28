import json

import pytest

from conductor.client.http.models.schema_def import SchemaDef, SchemaType
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("SchemaDef"))


def test_schema_def_serdes(server_json):
    schema_def = SchemaDef(
        name=server_json.get("name"),
        version=server_json.get("version"),
        type=SchemaType(server_json.get("type")) if server_json.get("type") else None,
        data=server_json.get("data"),
        external_ref=server_json.get("externalRef"),
    )
    schema_def.owner_app = server_json.get("ownerApp")
    schema_def.create_time = server_json.get("createTime")
    schema_def.update_time = server_json.get("updateTime")
    schema_def.created_by = server_json.get("createdBy")
    schema_def.updated_by = server_json.get("updatedBy")
    assert server_json.get("name") == schema_def.name
    assert server_json.get("version") == schema_def.version
    if server_json.get("type"):
        assert SchemaType(server_json.get("type")) == schema_def.type
    assert server_json.get("data") == schema_def.data
    assert server_json.get("externalRef") == schema_def.external_ref
    assert server_json.get("ownerApp") == schema_def.owner_app
    assert server_json.get("createTime") == schema_def.create_time
    assert server_json.get("updateTime") == schema_def.update_time
    assert server_json.get("createdBy") == schema_def.created_by
    assert server_json.get("updatedBy") == schema_def.updated_by
    model_dict = schema_def.to_dict()
    model_json = {}
    for attr, json_key in {**SchemaDef.attribute_map}.items():
        value = model_dict.get(attr)
        if value is not None:
            if attr == "type" and value is not None:
                model_json[json_key] = str(value)
            else:
                model_json[json_key] = value
    for key, value in server_json.items():
        if key == "type" and value is not None and model_json.get(key) is not None:
            assert value == model_json.get(key)
        else:
            assert value == model_json.get(key), f"Field {key} doesn't match"
