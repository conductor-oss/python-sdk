from typing import List

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.schema_def import SchemaDef
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.schema_client import SchemaClient

from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated


class OrkesSchemaClient(OrkesBaseClient, SchemaClient):
    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def register_schema(self, schema: SchemaDef, **kwargs) -> None:
        self._schema_api.save(schema, **kwargs)

    def get_schema(self, schema_name: str, version: int, **kwargs) -> SchemaDef:
        return self._schema_api.get_schema_by_name_and_version(
            name=schema_name, version=version, **kwargs
        )

    def get_all_schemas(self, **kwargs) -> List[SchemaDef]:
        return self._schema_api.get_all_schemas(**kwargs)

    @deprecated("delete_schema is deprecated; use delete_schema_by_name_and_version instead")
    @typing_deprecated("delete_schema is deprecated; use delete_schema_by_name_and_version instead")
    def delete_schema(self, schema_name: str, version: int, **kwargs) -> None:
        self._schema_api.delete_schema_by_name_and_version(
            name=schema_name, version=version, **kwargs
        )

    def delete_schema_by_name_and_version(self, schema_name: str, version: int, **kwargs) -> None:
        self._schema_api.delete_schema_by_name_and_version(
            name=schema_name, version=version, **kwargs
        )

    def delete_schema_by_name(self, schema_name: str, **kwargs) -> None:
        self._schema_api.delete_schema_by_name(name=schema_name, **kwargs)
