from typing import List

from conductor.client.configuration.configuration import Configuration
from conductor.client.adapters.models.schema_def_adapter import SchemaDefAdapter as SchemaDef
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.schema_client import SchemaClient


class OrkesSchemaClient(OrkesBaseClient, SchemaClient):
    def __init__(self, configuration: Configuration):
        super(OrkesSchemaClient, self).__init__(configuration)

    def register_schema(self, schema: SchemaDef) -> None:
        self.schemaApi.save(schema)

    def get_schema(self, schema_name: str, version: int) -> SchemaDef:
        return self.schemaApi.get_schema_by_name_and_version(name=schema_name, version=version)

    def get_all_schemas(self) -> List[SchemaDef]:
        return self.schemaApi.get_all_schemas()

    def delete_schema(self, schema_name: str, version: int) -> None:
        self.schemaApi.delete_schema_by_name_and_version(name=schema_name, version=version)

    def delete_schema_by_name(self, schema_name: str) -> None:
        self.schemaApi.delete_schema_by_name(name=schema_name)
