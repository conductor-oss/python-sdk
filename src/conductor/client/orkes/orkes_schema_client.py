from typing import List

from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.schema_def import SchemaDef
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.schema_client import SchemaClient


class OrkesSchemaClient(OrkesBaseClient, SchemaClient):
    def __init__(self, configuration: Configuration):
        """Initialize the OrkesSchemaClient with configuration.

        Args:
            configuration: Configuration object containing server settings and authentication

        Example:
            ```python
            from conductor.client.configuration.configuration import Configuration

            config = Configuration(server_api_url="http://localhost:8080/api")
            schema_client = OrkesSchemaClient(config)
            ```
        """
        super().__init__(configuration)

    def register_schema(self, schema: SchemaDef, **kwargs) -> None:
        """Register a schema definition.

        Args:
            schema: Schema definition to register
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.schema_def import SchemaDef

            schema = SchemaDef(
                name="order_schema",
                version=1,
                type="JSON",
                schema={
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "total": {"type": "number"}
                    }
                }
            )
            schema_client.register_schema(schema)
            ```
        """
        self._schema_api.save(body=schema, **kwargs)

    def get_schema(self, schema_name: str, version: int, **kwargs) -> SchemaDef:
        """Get a schema definition by name and version.

        Args:
            schema_name: Name of the schema
            version: Version number of the schema
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            SchemaDef instance

        Example:
            ```python
            schema = schema_client.get_schema("order_schema", 1)
            print(f"Schema: {schema.name}, Type: {schema.type}")
            ```
        """
        return self._schema_api.get_schema_by_name_and_version(
            name=schema_name, version=version, **kwargs
        )

    def get_all_schemas(self, **kwargs) -> List[SchemaDef]:
        """Get all registered schemas.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of SchemaDef instances

        Example:
            ```python
            schemas = schema_client.get_all_schemas()
            for schema in schemas:
                print(f"Schema: {schema.name}, Version: {schema.version}")
            ```
        """
        return self._schema_api.get_all_schemas(**kwargs)

    @deprecated("delete_schema is deprecated; use delete_schema_by_name_and_version instead")
    @typing_deprecated("delete_schema is deprecated; use delete_schema_by_name_and_version instead")
    def delete_schema(self, schema_name: str, version: int, **kwargs) -> None:
        """Delete a schema by name and version.

        .. deprecated::
            Use delete_schema_by_name_and_version() instead.

        Args:
            schema_name: Name of the schema to delete
            version: Version number of the schema
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None
        """
        self._schema_api.delete_schema_by_name_and_version(
            name=schema_name, version=version, **kwargs
        )

    def delete_schema_by_name_and_version(self, schema_name: str, version: int, **kwargs) -> None:
        """Delete a schema by name and version.

        Args:
            schema_name: Name of the schema to delete
            version: Version number of the schema
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            schema_client.delete_schema_by_name_and_version("old_schema", 1)
            ```
        """
        self._schema_api.delete_schema_by_name_and_version(
            name=schema_name, version=version, **kwargs
        )

    def delete_schema_by_name(self, schema_name: str, **kwargs) -> None:
        """Delete all versions of a schema by name.

        Args:
            schema_name: Name of the schema to delete (all versions)
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            schema_client.delete_schema_by_name("deprecated_schema")
            ```
        """
        self._schema_api.delete_schema_by_name(name=schema_name, **kwargs)
