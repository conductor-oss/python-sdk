from conductor.client.codegen.api.schema_resource_api import SchemaResourceApi
from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from typing import List
from conductor.client.http.models.schema_def import SchemaDef


class SchemaResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = SchemaResourceApi(api_client)

    def delete_schema_by_name(self, name: str, **kwargs) -> None:
        """Delete a schema by name"""
        return self._api.delete_schema_by_name(name, **kwargs)

    def delete_schema_by_name_and_version(self, name: str, version: int, **kwargs) -> None:
        """Delete a schema by name and version"""
        return self._api.delete_schema_by_name_and_version(name, version, **kwargs)

    def get_all_schemas(self, **kwargs) -> List[SchemaDef]:
        """Get all schemas"""
        return self._api.get_all_schemas(**kwargs)

    def get_schema_by_name_and_version(self, name: str, version: int, **kwargs) -> SchemaDef:
        """Get a schema by name and version"""
        return self._api.get_schema_by_name_and_version(name, version, **kwargs)

    def save(self, body: List[SchemaDef], **kwargs) -> None:
        """Save a schema"""
        return self._api.save(body, **kwargs)
