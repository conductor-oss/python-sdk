from typing import List

from conductor.asyncio_client.http.api import TagsApi
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter


class TagsApiAdapter(TagsApi):
    async def get_workflow_tags(self, *args, **kwargs) -> List[TagAdapter]:
        return await super().get_workflow_tags(*args, **kwargs)

    async def set_workflow_tags(
        self, workflow_name, body: List[TagAdapter], *args, **kwargs
    ) -> None:
        return await super().set_workflow_tags(workflow_name, body, *args, **kwargs)

    async def get_task_tags(self, *args, **kwargs) -> List[TagAdapter]:
        return await super().get_task_tags(*args, **kwargs)

    async def set_task_tags(self, task_name, body: List[TagAdapter], *args, **kwargs) -> None:
        return await super().set_task_tags(task_name, body, *args, **kwargs)
