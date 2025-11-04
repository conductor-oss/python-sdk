from __future__ import annotations

from typing import Dict, List, Optional

from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.models.save_schedule_request_adapter import (
    SaveScheduleRequestAdapter,
)
from conductor.asyncio_client.adapters.models.search_result_workflow_schedule_execution_model_adapter import (
    SearchResultWorkflowScheduleExecutionModelAdapter,
)
from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import (
    StartWorkflowRequestAdapter,
)
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.adapters.models.workflow_schedule_adapter import (
    WorkflowScheduleAdapter,
)
from conductor.asyncio_client.adapters.models.workflow_schedule_model_adapter import (
    WorkflowScheduleModelAdapter,
)
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient


class OrkesSchedulerClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        super().__init__(configuration, api_client)

    # Core Schedule Operations
    @deprecated("save_schedule is deprecated; use save_schedule_validated instead")
    @typing_deprecated("save_schedule is deprecated; use save_schedule_validated instead")
    async def save_schedule(self, save_schedule_request: SaveScheduleRequestAdapter) -> object:
        """Create or update a schedule for a specified workflow"""
        return await self._scheduler_api.save_schedule(save_schedule_request)

    async def save_schedule_validated(
        self, save_schedule_request: SaveScheduleRequestAdapter, **kwargs
    ) -> None:
        """Create or update a schedule for a specified workflow and return None"""
        await self._scheduler_api.save_schedule(
            save_schedule_request=save_schedule_request, **kwargs
        )

    async def get_schedule(self, name: str, **kwargs) -> WorkflowScheduleAdapter:
        """Get a workflow schedule by name"""
        return await self._scheduler_api.get_schedule(name=name, **kwargs)

    @deprecated("delete_schedule is deprecated; use delete_schedule_validated instead")
    @typing_deprecated("delete_schedule is deprecated; use delete_schedule_validated instead")
    async def delete_schedule(self, name: str) -> object:
        """Delete an existing workflow schedule by name"""
        return await self._scheduler_api.delete_schedule(name)

    async def delete_schedule_validated(self, name: str, **kwargs) -> None:
        """Delete an existing workflow schedule by name and return None"""
        await self._scheduler_api.delete_schedule(name=name, **kwargs)

    async def get_all_schedules(
        self, workflow_name: Optional[str] = None, **kwargs
    ) -> List[WorkflowScheduleModelAdapter]:
        """Get all workflow schedules, optionally filtered by workflow name"""
        return await self._scheduler_api.get_all_schedules(workflow_name=workflow_name, **kwargs)

    # Schedule Control Operations
    @deprecated("pause_schedule is deprecated; use pause_schedule_validated instead")
    @typing_deprecated("pause_schedule is deprecated; use pause_schedule_validated instead")
    async def pause_schedule(self, name: str) -> object:
        """Pause a workflow schedule"""
        return await self._scheduler_api.pause_schedule(name)

    async def pause_schedule_validated(self, name: str, **kwargs) -> None:
        """Pause a workflow schedule and return None"""
        await self._scheduler_api.pause_schedule(name=name, **kwargs)

    @deprecated("resume_schedule is deprecated; use resume_schedule_validated instead")
    @typing_deprecated("resume_schedule is deprecated; use resume_schedule_validated instead")
    async def resume_schedule(self, name: str) -> object:
        """Resume a paused workflow schedule"""
        return await self._scheduler_api.resume_schedule(name)

    async def resume_schedule_validated(self, name: str, **kwargs) -> None:
        """Resume a paused workflow schedule and return None"""
        await self._scheduler_api.resume_schedule(name=name, **kwargs)

    @deprecated("pause_all_schedules is deprecated; use pause_all_schedules_validated instead")
    @typing_deprecated(
        "pause_all_schedules is deprecated; use pause_all_schedules_validated instead"
    )
    async def pause_all_schedules(self) -> Dict[str, object]:
        """Pause all workflow schedules"""
        return await self._scheduler_api.pause_all_schedules()

    async def pause_all_schedules_validated(self, **kwargs) -> None:
        """Pause all workflow schedules and return None"""
        await self._scheduler_api.pause_all_schedules(**kwargs)

    @deprecated("resume_all_schedules is deprecated; use resume_all_schedules_validated instead")
    @typing_deprecated(
        "resume_all_schedules is deprecated; use resume_all_schedules_validated instead"
    )
    async def resume_all_schedules(self, **kwargs) -> Dict[str, object]:
        """Resume all paused workflow schedules"""
        return await self._scheduler_api.resume_all_schedules(**kwargs)

    async def resume_all_schedules_validated(self, **kwargs) -> None:
        """Resume all paused workflow schedules and return None"""
        await self._scheduler_api.resume_all_schedules(**kwargs)

    # Schedule Search and Discovery
    @deprecated("search_schedules is deprecated; use search_schedule_executions instead")
    @typing_deprecated("search_schedules is deprecated; use search_schedule_executions instead")
    async def search_schedules(
        self,
        start: int = 0,
        size: int = 100,
        sort: Optional[str] = None,
        free_text: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs,
    ) -> SearchResultWorkflowScheduleExecutionModelAdapter:
        """Search for workflow schedules with advanced filtering"""
        return await self._scheduler_api.search_v2(
            start=start, size=size, sort=sort, free_text=free_text, query=query, **kwargs
        )

    async def search_schedule_executions(
        self,
        start: Optional[int] = None,
        size: Optional[int] = None,
        sort: Optional[str] = None,
        free_text: Optional[str] = None,
        query: Optional[str] = None,
    ) -> SearchResultWorkflowScheduleExecutionModelAdapter:
        kwargs = {}
        if start:
            kwargs.update({"start": start})
        if size:
            kwargs.update({"size": size})
        if sort:
            kwargs.update({"sort": sort})
        if free_text:
            kwargs.update({"free_text": free_text})
        if query:
            kwargs.update({"query": query})
        return await self._scheduler_api.search_v2(**kwargs)

    async def get_schedules_by_tag(
        self, tag_value: str, **kwargs
    ) -> List[WorkflowScheduleModelAdapter]:
        """Get schedules filtered by tag key and value"""
        return await self._scheduler_api.get_schedules_by_tag(tag=tag_value, **kwargs)

    # Schedule Planning & Analysis
    @deprecated(
        "get_next_few_schedules is deprecated; use get_next_few_schedule_execution_times instead"
    )
    @typing_deprecated(
        "get_next_few_schedules is deprecated; use get_next_few_schedule_execution_times instead"
    )
    async def get_next_few_schedules(
        self,
        cron_expression: str,
        schedule_start_time: Optional[int] = None,
        schedule_end_time: Optional[int] = None,
        limit: Optional[int] = None,
        **kwargs,
    ) -> List[int]:
        """Get the next execution times for a cron expression"""
        return await self._scheduler_api.get_next_few_schedules(
            cron_expression=cron_expression,
            schedule_start_time=schedule_start_time,
            schedule_end_time=schedule_end_time,
            limit=limit,
            **kwargs,
        )

    # Tag Management for Schedules
    @deprecated("put_tag_for_schedule is deprecated; use set_tags_for_schedule instead")
    @typing_deprecated("put_tag_for_schedule is deprecated; use set_tags_for_schedule instead")
    async def put_tag_for_schedule(self, name: str, tags: List[TagAdapter], **kwargs) -> None:
        """Add tags to a workflow schedule"""
        await self._scheduler_api.put_tag_for_schedule(name=name, tag=tags, **kwargs)

    async def set_tags_for_schedule(self, name: str, tags: List[TagAdapter], **kwargs) -> None:
        """Set tags for a workflow schedule"""
        await self._scheduler_api.put_tag_for_schedule(name=name, tag=tags, **kwargs)

    @deprecated("get_tags_for_schedule is deprecated; use get_scheduler_tags instead")
    @typing_deprecated("get_tags_for_schedule is deprecated; use get_scheduler_tags instead")
    async def get_tags_for_schedule(self, name: str, **kwargs) -> List[TagAdapter]:
        """Get tags associated with a workflow schedule"""
        return await self._scheduler_api.get_tags_for_schedule(name, **kwargs)

    async def get_scheduler_tags(self, name: str, **kwargs) -> List[TagAdapter]:
        return await self._scheduler_api.get_tags_for_schedule(name=name, **kwargs)

    @deprecated("delete_tag_for_schedule is deprecated; use delete_scheduler_tags instead")
    @typing_deprecated("delete_tag_for_schedule is deprecated; use delete_scheduler_tags instead")
    async def delete_tag_for_schedule(self, name: str, tags: List[TagAdapter], **kwargs) -> None:
        """Delete specific tags from a workflow schedule"""
        await self._scheduler_api.delete_tag_for_schedule(name, tags, **kwargs)

    async def delete_scheduler_tags(self, tags: List[TagAdapter], name: str, **kwargs) -> None:
        await self._scheduler_api.delete_tag_for_schedule(name=name, tag=tags, **kwargs)

    # Schedule Execution Management
    @deprecated(
        "requeue_all_execution_records is deprecated; use requeue_all_execution_records_validated instead"
    )
    @typing_deprecated(
        "requeue_all_execution_records is deprecated; use requeue_all_execution_records_validated instead"
    )
    async def requeue_all_execution_records(self) -> Dict[str, object]:
        """Requeue all execution records for scheduled workflows"""
        return await self._scheduler_api.requeue_all_execution_records()

    async def requeue_all_execution_records_validated(self, **kwargs) -> None:
        """Requeue all execution records for scheduled workflows and return None"""
        await self._scheduler_api.requeue_all_execution_records(**kwargs)

    # Convenience Methods
    @deprecated("create_schedule is deprecated; use create_schedule_validated instead")
    @typing_deprecated("create_schedule is deprecated; use create_schedule_validated instead")
    async def create_schedule(
        self,
        name: str,
        cron_expression: str,
        workflow_name: str,
        workflow_version: Optional[int] = None,
        start_workflow_request: Optional[Dict] = None,
        timezone: Optional[str] = None,
        run_catch_up: bool = False,
    ) -> object:
        """Create a new workflow schedule with simplified parameters"""

        # Create the start workflow request if not provided
        if start_workflow_request is None:
            start_workflow_request = {}

        start_req = StartWorkflowRequestAdapter(
            name=workflow_name,
            version=workflow_version,
            input=start_workflow_request.get("input", {}),
            correlation_id=start_workflow_request.get("correlationId"),
            priority=start_workflow_request.get("priority"),
            task_to_domain=start_workflow_request.get("taskToDomain", {}),
        )

        save_request = SaveScheduleRequestAdapter(
            name=name,
            cron_expression=cron_expression,
            start_workflow_request=start_req,
            paused=False,
            run_catch_up=run_catch_up,
            timezone=timezone,
        )

        return await self.save_schedule(save_request)

    async def create_schedule_validated(
        self,
        name: str,
        cron_expression: str,
        workflow_name: str,
        workflow_version: Optional[int] = None,
        start_workflow_request: Optional[Dict] = None,
        timezone: Optional[str] = None,
        run_catch_up: bool = False,
        **kwargs,
    ) -> None:
        """Create a new workflow schedule with simplified parameters and return None"""
        # Create the start workflow request if not provided
        if start_workflow_request is None:
            start_workflow_request = {}

        start_req = StartWorkflowRequestAdapter(
            name=workflow_name,
            version=workflow_version,
            input=start_workflow_request.get("input", {}),
            correlation_id=start_workflow_request.get("correlationId"),
            priority=start_workflow_request.get("priority"),
            task_to_domain=start_workflow_request.get("taskToDomain", {}),
        )

        save_request = SaveScheduleRequestAdapter(
            name=name,
            cron_expression=cron_expression,
            start_workflow_request=start_req,
            paused=False,
            run_catch_up=run_catch_up,
            timezone=timezone,
        )
        await self.save_schedule_validated(save_schedule_request=save_request, **kwargs)

    @deprecated("update_schedule is deprecated; use update_schedule_validated instead")
    @typing_deprecated("update_schedule is deprecated; use update_schedule_validated instead")
    async def update_schedule(
        self,
        name: str,
        cron_expression: Optional[str] = None,
        paused: Optional[bool] = None,
        run_catch_up: Optional[bool] = None,
        timezone: Optional[str] = None,
        **kwargs,
    ) -> object:
        """Update an existing schedule with new parameters"""
        # Get the existing schedule
        existing_schedule = await self.get_schedule(name)

        # Create updated save request
        save_request = SaveScheduleRequestAdapter(
            name=name,
            cron_expression=cron_expression or existing_schedule.cron_expression,
            start_workflow_request=existing_schedule.start_workflow_request,
            paused=paused if paused is not None else existing_schedule.paused,
            run_catchup_schedule_instances=(
                run_catch_up
                if run_catch_up is not None
                else existing_schedule.run_catchup_schedule_instances
            ),
            zone_id=timezone or existing_schedule.zone_id,
        )

        return await self.save_schedule(save_request, **kwargs)

    async def update_schedule_validated(
        self,
        name: str,
        cron_expression: Optional[str] = None,
        paused: Optional[bool] = None,
        run_catch_up: Optional[bool] = None,
        timezone: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Update an existing schedule with new parameters and return None"""
        existing_schedule = await self.get_schedule(name=name, **kwargs)

        # Create updated save request
        save_request = SaveScheduleRequestAdapter(
            name=name,
            cron_expression=cron_expression or existing_schedule.cron_expression,
            start_workflow_request=existing_schedule.start_workflow_request,
            paused=paused if paused is not None else existing_schedule.paused,
            run_catchup_schedule_instances=(
                run_catch_up
                if run_catch_up is not None
                else existing_schedule.run_catchup_schedule_instances
            ),
            zone_id=timezone or existing_schedule.zone_id,
        )

        await self.save_schedule_validated(save_schedule_request=save_request, **kwargs)

    async def schedule_exists(self, name: str, **kwargs) -> bool:
        """Check if a schedule exists"""
        try:
            await self.get_schedule(name=name, **kwargs)
            return True
        except Exception:
            return False

    async def get_schedules_by_workflow(
        self, workflow_name: str, **kwargs
    ) -> List[WorkflowScheduleModelAdapter]:
        """Get all schedules for a specific workflow"""
        return await self.get_all_schedules(workflow_name=workflow_name, **kwargs)

    async def get_active_schedules(self, **kwargs) -> List[WorkflowScheduleModelAdapter]:
        """Get all active (non-paused) schedules"""
        all_schedules = await self.get_all_schedules(**kwargs)
        return [schedule for schedule in all_schedules if not schedule.paused]

    async def get_paused_schedules(self, **kwargs) -> List[WorkflowScheduleModelAdapter]:
        """Get all paused schedules"""
        all_schedules = await self.get_all_schedules(**kwargs)
        return [schedule for schedule in all_schedules if schedule.paused]

    async def bulk_pause_schedules(self, schedule_names: List[str], **kwargs) -> None:
        """Pause multiple schedules in bulk"""
        for name in schedule_names:
            try:
                await self.pause_schedule_validated(name=name, **kwargs)
            except Exception:  # noqa: PERF203
                continue

    async def bulk_resume_schedules(self, schedule_names: List[str], **kwargs) -> None:
        """Resume multiple schedules in bulk"""
        for name in schedule_names:
            try:
                await self.resume_schedule_validated(name=name, **kwargs)
            except Exception:  # noqa: PERF203
                continue

    async def bulk_delete_schedules(self, schedule_names: List[str], **kwargs) -> None:
        """Delete multiple schedules in bulk"""
        for name in schedule_names:
            try:
                await self.delete_schedule_validated(name=name, **kwargs)
            except Exception:  # noqa: PERF203
                continue

    async def validate_cron_expression(
        self, cron_expression: str, limit: int = 5, **kwargs
    ) -> List[int]:
        """Validate a cron expression by getting its next execution times"""
        return await self.get_next_few_schedule_execution_times(
            cron_expression=cron_expression, limit=limit, **kwargs
        )

    async def search_schedules_by_workflow(
        self, workflow_name: str, start: int = 0, size: int = 100, **kwargs
    ) -> SearchResultWorkflowScheduleExecutionModelAdapter:
        """Search schedules for a specific workflow"""
        return await self.search_schedule_executions(
            start=start, size=size, query=f"workflowName:{workflow_name}", **kwargs
        )

    async def search_schedules_by_status(
        self, paused: bool, start: int = 0, size: int = 100, **kwargs
    ) -> SearchResultWorkflowScheduleExecutionModelAdapter:
        """Search schedules by their status (paused/active)"""
        status_query = "paused:true" if paused else "paused:false"
        return await self.search_schedule_executions(
            start=start, size=size, query=status_query, **kwargs
        )

    async def get_schedule_count(self, **kwargs) -> int:
        """Get the total number of schedules"""
        schedules = await self.get_all_schedules(**kwargs)
        return len(schedules)

    async def get_schedules_with_tag(
        self, tag_value: str, **kwargs
    ) -> List[WorkflowScheduleModelAdapter]:
        """Get schedules that have a specific tag (alias for get_schedules_by_tag)"""
        return await self.get_schedules_by_tag(tag_value=tag_value, **kwargs)

    async def get_next_few_schedule_execution_times(
        self,
        cron_expression: str,
        schedule_start_time: Optional[int] = None,
        schedule_end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[int]:
        kwargs = {}
        if schedule_start_time:
            kwargs.update({"schedule_start_time": schedule_start_time})
        if schedule_end_time:
            kwargs.update({"schedule_end_time": schedule_end_time})
        if limit:
            kwargs.update({"limit": limit})
        return await self._scheduler_api.get_next_few_schedules(
            cron_expression=cron_expression, **kwargs
        )
