from typing import List

from conductor.asyncio_client.http.api import MetadataResourceApi
from conductor.asyncio_client.adapters.models.task_def_adapter import TaskDefAdapter
from conductor.asyncio_client.adapters.models.workflow_def_adapter import WorkflowDefAdapter
from conductor.asyncio_client.adapters.models.extended_workflow_def_adapter import (
    ExtendedWorkflowDefAdapter,
)


class MetadataResourceApiAdapter(MetadataResourceApi):
    async def get_task_def(self, *args, **kwargs) -> TaskDefAdapter:
        return await super().get_task_def(*args, **kwargs)

    async def get_task_defs(self, *args, **kwargs) -> List[TaskDefAdapter]:
        return await super().get_task_defs(*args, **kwargs)

    async def update(
        self, extended_workflow_def: List[ExtendedWorkflowDefAdapter], *args, **kwargs
    ) -> object:
        return await super().update(extended_workflow_def, *args, **kwargs)

    async def get(self, *args, **kwargs) -> WorkflowDefAdapter:
        return await super().get(*args, **kwargs)

    async def get_workflow_defs(self, *args, **kwargs) -> List[WorkflowDefAdapter]:
        return await super().get_workflow_defs(*args, **kwargs)
