from typing import List

from conductor.asyncio_client.http.api import GroupResourceApi
from conductor.asyncio_client.adapters.models.group_adapter import GroupAdapter


class GroupResourceApiAdapter(GroupResourceApi):
    async def list_groups(self, *args, **kwargs) -> List[GroupAdapter]:
        return await super().list_groups(*args, **kwargs)

    async def get_group(self, *args, **kwargs) -> GroupAdapter:
        return await super().get_group(*args, **kwargs)

    async def upsert_group(self, *args, **kwargs) -> GroupAdapter:
        return await super().upsert_group(*args, **kwargs)
