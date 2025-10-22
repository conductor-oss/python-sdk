from typing import List

from conductor.asyncio_client.http.api import SchemaResourceApi
from conductor.asyncio_client.adapters.models.schema_def_adapter import SchemaDefAdapter


class SchemaResourceApiAdapter(SchemaResourceApi):
    async def save(self, body: List[SchemaDefAdapter], *args, **kwargs) -> None:
        return await super().save(body, *args, **kwargs)

    async def get_schema_by_name_and_version(self, *args, **kwargs) -> SchemaDefAdapter:
        return await super().get_schema_by_name_and_version(*args, **kwargs)

    async def get_all_schemas(self, *args, **kwargs) -> List[SchemaDefAdapter]:
        return await super().get_all_schemas(*args, **kwargs)
