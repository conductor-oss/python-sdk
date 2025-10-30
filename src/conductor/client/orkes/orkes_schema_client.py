from typing import List

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.schema_def import SchemaDef
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.schema_client import SchemaClient


class OrkesSchemaClient(OrkesBaseClient, SchemaClient):
    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def register_schema(self, schema: SchemaDef) -> None:
        self._schema_api.save(schema)

    def get_schema(self, schema_name: str, version: int) -> SchemaDef:
        return self._schema_api.get_schema_by_name_and_version(name=schema_name, version=version)

    def get_all_schemas(self) -> List[SchemaDef]:
        return self._schema_api.get_all_schemas()

    def delete_schema(self, schema_name: str, version: int) -> None:
        self._schema_api.delete_schema_by_name_and_version(name=schema_name, version=version)

    def delete_schema_by_name(self, schema_name: str) -> None:
        self._schema_api.delete_schema_by_name(name=schema_name)
