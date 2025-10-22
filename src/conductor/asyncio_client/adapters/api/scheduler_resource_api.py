from typing import List

from conductor.asyncio_client.http.api import SchedulerResourceApi
from conductor.asyncio_client.adapters.models.workflow_schedule_adapter import (
    WorkflowScheduleAdapter,
)
from conductor.asyncio_client.adapters.models.workflow_schedule_model_adapter import (
    WorkflowScheduleModelAdapter,
)
from conductor.asyncio_client.adapters.models.search_result_workflow_schedule_execution_model_adapter import (
    SearchResultWorkflowScheduleExecutionModelAdapter,
)
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter


class SchedulerResourceApiAdapter(SchedulerResourceApi):
    async def get_schedule(self, *args, **kwargs) -> WorkflowScheduleAdapter:
        return await super().get_schedule(*args, **kwargs)

    async def get_all_schedules(self, *args, **kwargs) -> List[WorkflowScheduleModelAdapter]:
        return await super().get_all_schedules(*args, **kwargs)

    async def search_v2(self, *args, **kwargs) -> SearchResultWorkflowScheduleExecutionModelAdapter:
        return await super().search_v2(*args, **kwargs)

    async def get_schedules_by_tag(
        self, tag_key, tag_value, *args, **kwargs
    ) -> List[WorkflowScheduleModelAdapter]:
        return await super().get_schedules_by_tag(tag_key, tag_value, *args, **kwargs)

    async def put_tag_for_schedule(self, name, body: List[TagAdapter], *args, **kwargs) -> None:
        return await super().put_tag_for_schedule(name, body, *args, **kwargs)

    async def get_tags_for_schedule(self, *args, **kwargs) -> List[TagAdapter]:
        return await super().get_tags_for_schedule(*args, **kwargs)

    async def delete_tag_for_schedule(self, name, body: List[TagAdapter], *args, **kwargs) -> None:
        return await super().delete_tag_for_schedule(name, body, *args, **kwargs)
