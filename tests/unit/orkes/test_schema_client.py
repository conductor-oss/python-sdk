import logging
import pytest

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.schema_resource_api import SchemaResourceApi
from conductor.client.http.models.schema_def import SchemaDef
from conductor.client.orkes.orkes_schema_client import OrkesSchemaClient

SCHEMA_NAME = "ut_schema"
SCHEMA_VERSION = 1


@pytest.fixture(scope="module")
def schema_client():
    configuration = Configuration("http://localhost:8080/api")
    return OrkesSchemaClient(configuration)


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def schema_def():
    return SchemaDef(name=SCHEMA_NAME, version=SCHEMA_VERSION, data={})


def test_init(schema_client):
    message = "schemaApi is not of type SchemaApi"
    assert isinstance(schema_client.schemaApi, SchemaResourceApi), message


def test_register_schema(mocker, schema_client, schema_def):
    mock = mocker.patch.object(SchemaResourceApi, "save")
    schema_client.register_schema(schema_def)
    assert mock.called
    mock.assert_called_with(schema_def)


def test_get_schema(mocker, schema_client, schema_def):
    mock = mocker.patch.object(SchemaResourceApi, "get_schema_by_name_and_version")
    mock.return_value = schema_def
    schema = schema_client.get_schema(SCHEMA_NAME, SCHEMA_VERSION)
    assert schema == schema_def
    mock.assert_called_with(name=SCHEMA_NAME, version=SCHEMA_VERSION)


def test_get_all_schemas(mocker, schema_client, schema_def):
    mock = mocker.patch.object(SchemaResourceApi, "get_all_schemas")
    schema_def2 = SchemaDef(name="ut_schema_2", version=1)
    mock.return_value = [schema_def, schema_def2]
    schemas = schema_client.get_all_schemas()
    assert len(schemas) == 2


def test_delete_schema(mocker, schema_client, schema_def):
    mock = mocker.patch.object(SchemaResourceApi, "delete_schema_by_name_and_version")
    schema_client.delete_schema(SCHEMA_NAME, SCHEMA_VERSION)
    assert mock.called
    mock.assert_called_with(name=SCHEMA_NAME, version=SCHEMA_VERSION)


def test_delete_schema_by_name(mocker, schema_client):
    mock = mocker.patch.object(SchemaResourceApi, "delete_schema_by_name")
    schema_client.delete_schema_by_name(SCHEMA_NAME)
    assert mock.called
    mock.assert_called_with(name=SCHEMA_NAME)

