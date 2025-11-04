import os
import uuid
from copy import deepcopy

import pytest
import pytest_asyncio

from conductor.asyncio_client.adapters.api_client_adapter import \
    ApiClientAdapter as ApiClient
from conductor.asyncio_client.adapters.models.schema_def_adapter import \
    SchemaDefAdapter as SchemaDef
from conductor.asyncio_client.adapters.models.schema_def_adapter import \
    SchemaType
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.rest import ApiException
from conductor.asyncio_client.orkes.orkes_schema_client import \
    OrkesSchemaClient


class TestOrkesSchemaClientIntegration:
    """
    Integration tests for OrkesSchemaClient.

    Environment Variables:
    - CONDUCTOR_SERVER_URL: Base URL for Conductor server (default: http://localhost:8080/api)
    - CONDUCTOR_AUTH_KEY: Authentication key for Orkes
    - CONDUCTOR_AUTH_SECRET: Authentication secret for Orkes
    - CONDUCTOR_UI_SERVER_URL: UI server URL (optional)
    - CONDUCTOR_TEST_TIMEOUT: Test timeout in seconds (default: 30)
    - CONDUCTOR_TEST_CLEANUP: Whether to cleanup test resources (default: true)
    """

    @pytest.fixture(scope="class")
    def configuration(self) -> Configuration:
        config = Configuration()
        config.debug = os.getenv("CONDUCTOR_DEBUG", "false").lower() == "true"
        config.apply_logging_config()
        return config

    @pytest_asyncio.fixture(scope="function")
    async def schema_client(self, configuration: Configuration) -> OrkesSchemaClient:
        async with ApiClient(configuration) as api_client:
            return OrkesSchemaClient(configuration, api_client)

    @pytest.fixture(scope="class")
    def test_suffix(self) -> str:
        return str(uuid.uuid4())[:8]

    @pytest.fixture(scope="class")
    def test_schema_name(self, test_suffix: str) -> str:
        return f"test_schema_{test_suffix}"

    @pytest.fixture(scope="class")
    def json_schema_data(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "active": {"type": "boolean"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["id", "name", "email"],
            "$schema": "http://json-schema.org/draft-07/schema",
        }

    @pytest.fixture(scope="class")
    def avro_schema_data(self) -> dict:
        return {
            "type": "record",
            "name": "User",
            "namespace": "com.example",
            "fields": [
                {"name": "id", "type": "int"},
                {"name": "name", "type": "string"},
                {"name": "email", "type": "string"},
                {"name": "active", "type": "boolean", "default": True},
            ],
        }

    @pytest.fixture(scope="class")
    def protobuf_schema_data(self) -> dict:
        return {
            "syntax": "proto3",
            "package": "com.example",
            "message": {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "int32", "number": 1},
                    {"name": "name", "type": "string", "number": 2},
                    {"name": "email", "type": "string", "number": 3},
                    {"name": "active", "type": "bool", "number": 4},
                ],
            },
        }

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_schema_lifecycle_json(
        self,
        schema_client: OrkesSchemaClient,
        test_schema_name: str,
        json_schema_data: dict,
    ):
        try:
            schema = SchemaDef(
                name=test_schema_name,
                version=1,
                type=SchemaType.JSON,
                data=json_schema_data,
                external_ref="http://example.com/json-schema",
            )

            await schema_client.save_schema(schema)

            retrieved_schema = await schema_client.get_schema(test_schema_name, 1)
            assert retrieved_schema.name == test_schema_name
            assert retrieved_schema.version == 1
            assert retrieved_schema.type == SchemaType.JSON
            assert retrieved_schema.data == json_schema_data
            assert (
                retrieved_schema.data["$schema"]
                == "http://json-schema.org/draft-07/schema"
            )

            schemas = await schema_client.get_all_schemas()
            schema_names = [s.name for s in schemas]
            assert test_schema_name in schema_names

        except Exception as e:
            print(f"Exception in test_schema_lifecycle_json: {str(e)}")
            raise
        finally:
            try:
                await schema_client.delete_schema(test_schema_name, 1)
            except Exception as e:
                print(f"Warning: Failed to cleanup schema {test_schema_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_schema_lifecycle_avro(
        self, schema_client: OrkesSchemaClient, test_suffix: str, avro_schema_data: dict
    ):
        schema_name = f"test_avro_schema_{test_suffix}"
        try:
            schema = SchemaDef(
                name=schema_name,
                version=1,
                type=SchemaType.AVRO,
                data=avro_schema_data,
                external_ref="http://example.com/avro-schema",
            )

            await schema_client.save_schema(schema)

            retrieved_schema = await schema_client.get_schema(schema_name, 1)
            assert retrieved_schema.name == schema_name
            assert retrieved_schema.version == 1
            assert retrieved_schema.type == SchemaType.AVRO
            assert retrieved_schema.data == avro_schema_data

        except Exception as e:
            print(f"Exception in test_schema_lifecycle_avro: {str(e)}")
            raise
        finally:
            try:
                await schema_client.delete_schema(schema_name, 1)
            except Exception as e:
                print(f"Warning: Failed to cleanup schema {schema_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_schema_lifecycle_protobuf(
        self,
        schema_client: OrkesSchemaClient,
        test_suffix: str,
        protobuf_schema_data: dict,
    ):
        schema_name = f"test_protobuf_schema_{test_suffix}"
        try:
            schema = SchemaDef(
                name=schema_name,
                version=1,
                type=SchemaType.PROTOBUF,
                data=protobuf_schema_data,
                external_ref="http://example.com/protobuf-schema",
            )

            await schema_client.save_schema(schema)

            retrieved_schema = await schema_client.get_schema(schema_name, 1)
            assert retrieved_schema.name == schema_name
            assert retrieved_schema.version == 1
            assert retrieved_schema.type == SchemaType.PROTOBUF
            assert retrieved_schema.data == protobuf_schema_data

        except Exception as e:
            print(f"Exception in test_schema_lifecycle_protobuf: {str(e)}")
            raise
        finally:
            try:
                await schema_client.delete_schema(schema_name, 1)
            except Exception as e:
                print(f"Warning: Failed to cleanup schema {schema_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_schema_versioning(
        self, schema_client: OrkesSchemaClient, test_suffix: str, json_schema_data: dict
    ):
        schema_name = f"test_versioned_schema_{test_suffix}"
        try:
            schema_v1 = SchemaDef(
                name=schema_name,
                version=1,
                type=SchemaType.JSON,
                data=json_schema_data,
                external_ref="http://example.com/v1",
            )
            schema_v2_data = deepcopy(json_schema_data)
            schema_v2_data["properties"]["age"] = {"type": "integer"}
            schema_v2 = SchemaDef(
                name=schema_name,
                version=2,
                type=SchemaType.JSON,
                data=schema_v2_data,
                external_ref="http://example.com/v2",
            )

            await schema_client.save_schema(schema_v1)
            await schema_client.save_schema(schema_v2)

            retrieved_v1 = await schema_client.get_schema(schema_name, 1)
            assert retrieved_v1.version == 1
            assert "age" not in retrieved_v1.data["properties"].keys()

            retrieved_v2 = await schema_client.get_schema(schema_name, 2)
            assert retrieved_v2.version == 2
            assert "age" in retrieved_v2.data["properties"].keys()

        except Exception as e:
            print(f"Exception in test_schema_versioning: {str(e)}")
            raise
        finally:
            try:
                await schema_client.delete_schema(schema_name, 1)
                await schema_client.delete_schema(schema_name, 2)
            except Exception as e:
                print(f"Warning: Failed to cleanup schema {schema_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_delete_schema_by_name(
        self, schema_client: OrkesSchemaClient, test_suffix: str, json_schema_data: dict
    ):
        schema_name = f"test_delete_by_name_{test_suffix}"
        try:
            schema_v1 = SchemaDef(
                name=schema_name, version=1, type=SchemaType.JSON, data=json_schema_data
            )

            schema_v2 = SchemaDef(
                name=schema_name, version=2, type=SchemaType.JSON, data=json_schema_data
            )

            await schema_client.save_schema(schema_v1)
            await schema_client.save_schema(schema_v2)

            await schema_client.delete_schema_by_name(schema_name)

            with pytest.raises(ApiException) as exc_info:
                await schema_client.get_schema(schema_name, 1)
            assert exc_info.value.status == 404

            with pytest.raises(ApiException) as exc_info:
                await schema_client.get_schema(schema_name, 2)
            assert exc_info.value.status == 404

        except Exception as e:
            print(f"Exception in test_delete_schema_by_name: {str(e)}")
            raise

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_complex_schema_management_flow(
        self, schema_client: OrkesSchemaClient, test_suffix: str
    ):
        created_resources = {"schemas": []}

        try:
            schema_types = [SchemaType.JSON, SchemaType.AVRO, SchemaType.PROTOBUF]
            schema_templates = {
                SchemaType.JSON: {
                    "type": "object",
                    "properties": {"field": {"type": "string"}},
                    "$schema": "http://json-schema.org/draft-07/schema",
                },
                SchemaType.AVRO: {
                    "type": "record",
                    "name": "TestRecord",
                    "fields": [{"name": "field", "type": "string"}],
                },
                SchemaType.PROTOBUF: {
                    "syntax": "proto3",
                    "message": {
                        "name": "TestMessage",
                        "fields": [{"name": "field", "type": "string", "number": 1}],
                    },
                },
            }

            for schema_type in schema_types:
                for version in range(1, 4):
                    schema_name = f"complex_{schema_type}_v{version}_{test_suffix}"
                    schema = SchemaDef(
                        name=schema_name,
                        version=version,
                        type=schema_type,
                        data=schema_templates[schema_type],
                        external_ref=f"http://example.com/{schema_type}/v{version}",
                    )

                    await schema_client.save_schema(schema)
                    created_resources["schemas"].append((schema_name, version))

            all_schemas = await schema_client.get_all_schemas()
            schema_names = [s.name for s in all_schemas]
            for schema_name, version in created_resources["schemas"]:
                assert (
                    schema_name in schema_names
                ), f"Schema {schema_name} not found in list"

            for schema_type in schema_types:
                for version in range(1, 4):
                    schema_name = f"complex_{schema_type}_v{version}_{test_suffix}"
                    retrieved_schema = await schema_client.get_schema(
                        schema_name, version
                    )
                    assert retrieved_schema.name == schema_name
                    assert retrieved_schema.version == version
                    assert retrieved_schema.type == schema_type

            bulk_schemas = []
            for i in range(5):
                schema_name = f"bulk_schema_{i}_{test_suffix}"
                schema = SchemaDef(
                    name=schema_name,
                    version=1,
                    type=SchemaType.JSON,
                    data={"type": "object", "properties": {"id": {"type": "integer"}}},
                )
                await schema_client.save_schema(schema)
                bulk_schemas.append(schema_name)
                created_resources["schemas"].append((schema_name, 1))

            all_schemas_after_bulk = await schema_client.get_all_schemas()
            schema_names_after_bulk = [s.name for s in all_schemas_after_bulk]
            for schema_name in bulk_schemas:
                assert (
                    schema_name in schema_names_after_bulk
                ), f"Bulk schema {schema_name} not found in list"

        except Exception as e:
            print(f"Exception in test_complex_schema_management_flow: {str(e)}")
            raise
        finally:
            await self._perform_comprehensive_cleanup(schema_client, created_resources)

    async def _perform_comprehensive_cleanup(
        self, schema_client: OrkesSchemaClient, created_resources: dict
    ):
        cleanup_enabled = os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true"
        if not cleanup_enabled:
            return

        for schema_name, version in created_resources["schemas"]:
            try:
                await schema_client.delete_schema(schema_name, version)
            except Exception as e:
                print(
                    f"Warning: Failed to delete schema {schema_name} v{version}: {str(e)}"
                )

        remaining_schemas = []
        for schema_name, version in created_resources["schemas"]:
            try:
                await schema_client.get_schema(schema_name, version)
                remaining_schemas.append((schema_name, version))
            except ApiException as e:
                if e.status == 404:
                    pass
                else:
                    remaining_schemas.append((schema_name, version))
            except Exception:
                remaining_schemas.append((schema_name, version))

        if remaining_schemas:
            print(
                f"Warning: {len(remaining_schemas)} schemas could not be verified as deleted: {remaining_schemas}"
            )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_schema_register_methods(
        self, schema_client: OrkesSchemaClient, test_suffix: str, json_schema_data: dict
    ):
        """Test register schema methods."""
        schema_name = f"register_schema_{test_suffix}"

        try:
            schema_def = SchemaDef(
                name=schema_name,
                version=1,
                type=SchemaType.JSON,
                data=json_schema_data,
            )

            await schema_client.register_schema(schema_def)

            retrieved_schema = await schema_client.get_schema(schema_name, 1)
            assert retrieved_schema is not None
            assert retrieved_schema.name == schema_name
            assert retrieved_schema.version == 1

            schema_def_v2 = SchemaDef(
                name=schema_name,
                version=2,
                type=SchemaType.JSON,
                data=json_schema_data,
            )

            await schema_client.register_schemas([schema_def_v2], new_version=True)

            retrieved_schema_v2 = await schema_client.get_schema(schema_name, 2)
            assert retrieved_schema_v2 is not None
            assert retrieved_schema_v2.version == 2
        except Exception as e:
            print(f"Exception in test_schema_register_methods: {str(e)}")
            raise
        finally:
            try:
                await schema_client.delete_schema_by_name(schema_name)
            except Exception:
                pass
