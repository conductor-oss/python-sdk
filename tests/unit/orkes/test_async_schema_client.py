import logging

import pytest

from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.adapters.api.schema_resource_api import SchemaResourceApiAdapter
from conductor.asyncio_client.adapters.models.schema_def_adapter import SchemaDefAdapter
from conductor.asyncio_client.http.rest import ApiException
from conductor.asyncio_client.orkes.orkes_schema_client import OrkesSchemaClient
from conductor.asyncio_client.adapters import ApiClient

SCHEMA_NAME = "ut_schema"
SCHEMA_VERSION = 1


@pytest.fixture(scope="module")
def schema_client():
    configuration = Configuration("http://localhost:8080/api")
    api_client = ApiClient(configuration)
    return OrkesSchemaClient(configuration, api_client=api_client)


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def schema_def_adapter():
    return SchemaDefAdapter(
        name=SCHEMA_NAME,
        version=SCHEMA_VERSION,
        type="JSON",
        data={"schema": {"type": "object", "properties": {}}}
    )


@pytest.mark.asyncio
async def test_init(schema_client):
    message = "schema_api is not of type SchemaResourceApiAdapter"
    assert isinstance(schema_client.schema_api, SchemaResourceApiAdapter), message


@pytest.mark.asyncio
async def test_save_schema(mocker, schema_client, schema_def_adapter):
    mock = mocker.patch.object(SchemaResourceApiAdapter, "save")
    await schema_client.save_schema(schema_def_adapter)
    mock.assert_called_with([schema_def_adapter], new_version=None)


@pytest.mark.asyncio
async def test_save_schema_with_new_version(mocker, schema_client, schema_def_adapter):
    mock = mocker.patch.object(SchemaResourceApiAdapter, "save")
    await schema_client.save_schema(schema_def_adapter, new_version=True)
    mock.assert_called_with([schema_def_adapter], new_version=True)


@pytest.mark.asyncio
async def test_save_schemas(mocker, schema_client, schema_def_adapter):
    mock = mocker.patch.object(SchemaResourceApiAdapter, "save")
    schemas = [schema_def_adapter]
    await schema_client.save_schemas(schemas)
    mock.assert_called_with(schemas, new_version=None)


@pytest.mark.asyncio
async def test_get_schema(mocker, schema_client, schema_def_adapter):
    mock = mocker.patch.object(SchemaResourceApiAdapter, "get_schema_by_name_and_version")
    mock.return_value = schema_def_adapter
    result = await schema_client.get_schema(SCHEMA_NAME, SCHEMA_VERSION)
    mock.assert_called_with(SCHEMA_NAME, SCHEMA_VERSION)
    assert result == schema_def_adapter


@pytest.mark.asyncio
async def test_get_all_schemas(mocker, schema_client, schema_def_adapter):
    mock = mocker.patch.object(SchemaResourceApiAdapter, "get_all_schemas")
    schema_def2 = SchemaDefAdapter(name="ut_schema_2", version=1, type="JSON", data={"schema": {}})
    mock.return_value = [schema_def_adapter, schema_def2]
    result = await schema_client.get_all_schemas()
    assert mock.called
    assert result == [schema_def_adapter, schema_def2]


@pytest.mark.asyncio
async def test_delete_schema_by_name_and_version(mocker, schema_client):
    mock = mocker.patch.object(SchemaResourceApiAdapter, "delete_schema_by_name_and_version")
    await schema_client.delete_schema_by_name_and_version(SCHEMA_NAME, SCHEMA_VERSION)
    mock.assert_called_with(SCHEMA_NAME, SCHEMA_VERSION)


@pytest.mark.asyncio
async def test_delete_schema_by_name(mocker, schema_client):
    mock = mocker.patch.object(SchemaResourceApiAdapter, "delete_schema_by_name")
    await schema_client.delete_schema_by_name(SCHEMA_NAME)
    mock.assert_called_with(SCHEMA_NAME)


@pytest.mark.asyncio
async def test_schema_exists_true(mocker, schema_client):
    mock = mocker.patch.object(schema_client, "get_schema")
    mock.return_value = SchemaDefAdapter(name=SCHEMA_NAME, version=SCHEMA_VERSION, type="JSON")
    result = await schema_client.schema_exists(SCHEMA_NAME, SCHEMA_VERSION)
    assert result is True


@pytest.mark.asyncio
async def test_schema_exists_false(mocker, schema_client):
    mock = mocker.patch.object(schema_client, "get_schema")
    mock.side_effect = ApiException(status=404, body="Schema not found")
    result = await schema_client.schema_exists(SCHEMA_NAME, SCHEMA_VERSION)
    assert result is False


@pytest.mark.asyncio
async def test_get_latest_schema_version(mocker, schema_client):
    mock = mocker.patch.object(schema_client, "get_all_schemas")
    schema1 = SchemaDefAdapter(name=SCHEMA_NAME, version=1, type="JSON", data={})
    schema2 = SchemaDefAdapter(name=SCHEMA_NAME, version=2, type="JSON", data={})
    schema3 = SchemaDefAdapter(name="other_schema", version=1, type="JSON", data={})
    mock.return_value = [schema1, schema2, schema3]
    result = await schema_client.get_latest_schema_version(SCHEMA_NAME)
    assert result == schema2


@pytest.mark.asyncio
async def test_get_latest_schema_version_not_found(mocker, schema_client):
    mock = mocker.patch.object(schema_client, "get_all_schemas")
    schema = SchemaDefAdapter(name="other_schema", version=1, type="JSON", data={})
    mock.return_value = [schema]
    result = await schema_client.get_latest_schema_version(SCHEMA_NAME)
    assert result is None


@pytest.mark.asyncio
async def test_get_schema_versions(mocker, schema_client):
    mock = mocker.patch.object(schema_client, "get_all_schemas")
    schema1 = SchemaDefAdapter(name=SCHEMA_NAME, version=1, type="JSON", data={})
    schema2 = SchemaDefAdapter(name=SCHEMA_NAME, version=2, type="JSON", data={})
    schema3 = SchemaDefAdapter(name=SCHEMA_NAME, version=3, type="JSON", data={})
    mock.return_value = [schema1, schema2, schema3]
    result = await schema_client.get_schema_versions(SCHEMA_NAME)
    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_get_schemas_by_name(mocker, schema_client):
    mock = mocker.patch.object(schema_client, "get_all_schemas")
    schema1 = SchemaDefAdapter(name=SCHEMA_NAME, version=1, type="JSON", data={})
    schema2 = SchemaDefAdapter(name=SCHEMA_NAME, version=2, type="JSON", data={})
    schema3 = SchemaDefAdapter(name="other_schema", version=1, type="JSON", data={})
    mock.return_value = [schema1, schema2, schema3]
    result = await schema_client.get_schemas_by_name(SCHEMA_NAME)
    assert result == [schema1, schema2]


@pytest.mark.asyncio
async def test_get_schema_count(mocker, schema_client):
    mock = mocker.patch.object(schema_client, "get_all_schemas")
    schemas = [
        SchemaDefAdapter(name="schema1", version=1, type="JSON", data={}),
        SchemaDefAdapter(name="schema2", version=1, type="JSON", data={}),
        SchemaDefAdapter(name="schema3", version=1, type="JSON", data={})
    ]
    mock.return_value = schemas
    result = await schema_client.get_schema_count()
    assert result == 3


@pytest.mark.asyncio
async def test_get_unique_schema_names(mocker, schema_client):
    mock = mocker.patch.object(schema_client, "get_all_schemas")
    schemas = [
        SchemaDefAdapter(name="schema1", version=1, type="JSON", data={}),
        SchemaDefAdapter(name="schema2", version=1, type="JSON", data={}),
        SchemaDefAdapter(name="schema1", version=2, type="JSON", data={})
    ]
    mock.return_value = schemas
    result = await schema_client.get_unique_schema_names()
    assert result == ["schema1", "schema2"]


@pytest.mark.asyncio
async def test_delete_all_schema_versions(mocker, schema_client):
    mock = mocker.patch.object(schema_client, "delete_schema_by_name")
    await schema_client.delete_all_schema_versions(SCHEMA_NAME)
    mock.assert_called_with(SCHEMA_NAME)


@pytest.mark.asyncio
async def test_search_schemas_by_name(mocker, schema_client):
    mock = mocker.patch.object(schema_client, "get_all_schemas")
    schemas = [
        SchemaDefAdapter(name="user_schema", version=1, type="JSON", data={}),
        SchemaDefAdapter(name="order_schema", version=1, type="JSON", data={}),
        SchemaDefAdapter(name="product_schema", version=1, type="JSON", data={})
    ]
    mock.return_value = schemas
    result = await schema_client.search_schemas_by_name("user")
    assert result == [schemas[0]]


@pytest.mark.asyncio
async def test_validate_schema_structure_valid(schema_client):
    schema_definition = {"type": "object", "properties": {"name": {"type": "string"}}}
    result = await schema_client.validate_schema_structure(schema_definition)
    assert result is True


@pytest.mark.asyncio
async def test_validate_schema_structure_invalid(schema_client):
    schema_definition = {}
    result = await schema_client.validate_schema_structure(schema_definition)
    assert result is False


@pytest.mark.asyncio
async def test_list_schemas(mocker, schema_client):
    mock = mocker.patch.object(schema_client, "get_all_schemas")
    schemas = [SchemaDefAdapter(name="schema1", version=1, type="JSON", data={})]
    mock.return_value = schemas
    result = await schema_client.list_schemas()
    assert result == schemas


@pytest.mark.asyncio
async def test_delete_schema_with_version(mocker, schema_client):
    mock = mocker.patch.object(schema_client, "delete_schema_by_name_and_version")
    await schema_client.delete_schema(SCHEMA_NAME, SCHEMA_VERSION)
    mock.assert_called_with(SCHEMA_NAME, SCHEMA_VERSION)


@pytest.mark.asyncio
async def test_delete_schema_without_version(mocker, schema_client):
    mock = mocker.patch.object(schema_client, "delete_schema_by_name")
    await schema_client.delete_schema(SCHEMA_NAME)
    mock.assert_called_with(SCHEMA_NAME)


@pytest.mark.asyncio
async def test_create_schema_version(mocker, schema_client):
    mock_versions = mocker.patch.object(schema_client, "get_schema_versions")
    mock_create = mocker.patch.object(schema_client, "create_schema")
    mock_versions.return_value = [1, 2, 3]
    schema_definition = {"type": "object", "properties": {"name": {"type": "string"}}}
    await schema_client.create_schema_version(SCHEMA_NAME, schema_definition, "New version")
    mock_create.assert_called_with(SCHEMA_NAME, 4, schema_definition, "New version")


@pytest.mark.asyncio
async def test_create_schema_version_first_version(mocker, schema_client):
    mock_versions = mocker.patch.object(schema_client, "get_schema_versions")
    mock_create = mocker.patch.object(schema_client, "create_schema")
    mock_versions.return_value = []
    schema_definition = {"type": "object", "properties": {"name": {"type": "string"}}}
    await schema_client.create_schema_version(SCHEMA_NAME, schema_definition, "First version")
    mock_create.assert_called_with(SCHEMA_NAME, 1, schema_definition, "First version")


@pytest.mark.asyncio
async def test_get_schema_api_exception(mocker, schema_client):
    mock = mocker.patch.object(SchemaResourceApiAdapter, "get_schema_by_name_and_version")
    mock.side_effect = ApiException(status=404, body="Schema not found")
    with pytest.raises(ApiException):
        await schema_client.get_schema(SCHEMA_NAME, SCHEMA_VERSION)
    mock.assert_called_with(SCHEMA_NAME, SCHEMA_VERSION)


@pytest.mark.asyncio
async def test_save_schema_api_exception(mocker, schema_client, schema_def_adapter):
    mock = mocker.patch.object(SchemaResourceApiAdapter, "save")
    mock.side_effect = ApiException(status=400, body="Bad request")
    with pytest.raises(ApiException):
        await schema_client.save_schema(schema_def_adapter)
    mock.assert_called_with([schema_def_adapter], new_version=None)


@pytest.mark.asyncio
async def test_delete_schema_api_exception(mocker, schema_client):
    mock = mocker.patch.object(SchemaResourceApiAdapter, "delete_schema_by_name_and_version")
    mock.side_effect = ApiException(status=404, body="Schema not found")
    with pytest.raises(ApiException):
        await schema_client.delete_schema_by_name_and_version(SCHEMA_NAME, SCHEMA_VERSION)
    mock.assert_called_with(SCHEMA_NAME, SCHEMA_VERSION)


@pytest.mark.asyncio
async def test_get_all_schemas_api_exception(mocker, schema_client):
    mock = mocker.patch.object(SchemaResourceApiAdapter, "get_all_schemas")
    mock.side_effect = ApiException(status=500, body="Internal error")
    with pytest.raises(ApiException):
        await schema_client.get_all_schemas()
    assert mock.called


@pytest.mark.asyncio
async def test_search_schemas_by_name_case_insensitive(mocker, schema_client):
    mock = mocker.patch.object(schema_client, "get_all_schemas")
    schemas = [
        SchemaDefAdapter(name="UserSchema", version=1, type="JSON", data={}),
        SchemaDefAdapter(name="OrderSchema", version=1, type="JSON", data={})
    ]
    mock.return_value = schemas
    result = await schema_client.search_schemas_by_name("user")
    assert result == [schemas[0]]
