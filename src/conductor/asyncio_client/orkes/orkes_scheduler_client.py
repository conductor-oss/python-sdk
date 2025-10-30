from __future__ import annotations

from typing import Dict, List, Optional

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
    async def save_schedule(self, save_schedule_request: SaveScheduleRequestAdapter) -> object:
        """Create or update a schedule for a specified workflow"""
        return await self.scheduler_api.save_schedule(save_schedule_request)

    async def get_schedule(self, name: str) -> WorkflowScheduleAdapter:
        """Get a workflow schedule by name"""
        return await self.scheduler_api.get_schedule(name)

    async def delete_schedule(self, name: str) -> object:
        """Delete an existing workflow schedule by name"""
        return await self.scheduler_api.delete_schedule(name)

    async def get_all_schedules(
        self, workflow_name: Optional[str] = None
    ) -> List[WorkflowScheduleModelAdapter]:
        """Get all workflow schedules, optionally filtered by workflow name"""
        return await self.scheduler_api.get_all_schedules(workflow_name=workflow_name)

    # Schedule Control Operations
    async def pause_schedule(self, name: str) -> object:
        """Pause a workflow schedule"""
        return await self.scheduler_api.pause_schedule(name)

    async def resume_schedule(self, name: str) -> object:
        """Resume a paused workflow schedule"""
        return await self.scheduler_api.resume_schedule(name)

    async def pause_all_schedules(self) -> Dict[str, object]:
        """Pause all workflow schedules"""
        return await self.scheduler_api.pause_all_schedules()

    async def resume_all_schedules(self) -> Dict[str, object]:
        """Resume all paused workflow schedules"""
        return await self.scheduler_api.resume_all_schedules()

    # Schedule Search and Discovery
    async def search_schedules(
        self,
        start: int = 0,
        size: int = 100,
        sort: Optional[str] = None,
        free_text: Optional[str] = None,
        query: Optional[str] = None,
    ) -> SearchResultWorkflowScheduleExecutionModelAdapter:
        """Search for workflow schedules with advanced filtering"""
        return await self.scheduler_api.search_v2(
            start=start, size=size, sort=sort, free_text=free_text, query=query
        )

    async def get_schedules_by_tag(self, tag_value: str) -> List[WorkflowScheduleModelAdapter]:
        """Get schedules filtered by tag key and value"""
        return await self.scheduler_api.get_schedules_by_tag(tag_value)

    # Schedule Planning & Analysis
    async def get_next_few_schedules(
        self,
        cron_expression: str,
        schedule_start_time: Optional[int] = None,
        schedule_end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[int]:
        """Get the next execution times for a cron expression"""
        return await self.scheduler_api.get_next_few_schedules(
            cron_expression=cron_expression,
            schedule_start_time=schedule_start_time,
            schedule_end_time=schedule_end_time,
            limit=limit,
        )

    # Tag Management for Schedules
    async def put_tag_for_schedule(self, name: str, tags: List[TagAdapter]) -> None:
        """Add tags to a workflow schedule"""
        await self.scheduler_api.put_tag_for_schedule(name, tags)

    async def get_tags_for_schedule(self, name: str) -> List[TagAdapter]:
        """Get tags associated with a workflow schedule"""
        return await self.scheduler_api.get_tags_for_schedule(name)

    async def delete_tag_for_schedule(self, name: str, tags: List[TagAdapter]) -> None:
        """Delete specific tags from a workflow schedule"""
        await self.scheduler_api.delete_tag_for_schedule(name, tags)

    # Schedule Execution Management
    async def requeue_all_execution_records(self) -> Dict[str, object]:
        """Requeue all execution records for scheduled workflows"""
        return await self.scheduler_api.requeue_all_execution_records()

    # Convenience Methods
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

    async def update_schedule(
        self,
        name: str,
        cron_expression: Optional[str] = None,
        paused: Optional[bool] = None,
        run_catch_up: Optional[bool] = None,
        timezone: Optional[str] = None,
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

        return await self.save_schedule(save_request)

    async def schedule_exists(self, name: str) -> bool:
        """Check if a schedule exists"""
        try:
            await self.get_schedule(name)
            return True
        except Exception:
            return False

    async def get_schedules_by_workflow(
        self, workflow_name: str
    ) -> List[WorkflowScheduleModelAdapter]:
        """Get all schedules for a specific workflow"""
        return await self.get_all_schedules(workflow_name=workflow_name)

    async def get_active_schedules(self) -> List[WorkflowScheduleModelAdapter]:
        """Get all active (non-paused) schedules"""
        all_schedules = await self.get_all_schedules()
        return [schedule for schedule in all_schedules if not schedule.paused]

    async def get_paused_schedules(self) -> List[WorkflowScheduleModelAdapter]:
        """Get all paused schedules"""
        all_schedules = await self.get_all_schedules()
        return [schedule for schedule in all_schedules if schedule.paused]

    async def bulk_pause_schedules(self, schedule_names: List[str]) -> None:
        """Pause multiple schedules in bulk"""
        for name in schedule_names:
            try:
                await self.pause_schedule(name)
            except Exception:  # noqa: PERF203
                continue

    async def bulk_resume_schedules(self, schedule_names: List[str]) -> None:
        """Resume multiple schedules in bulk"""
        for name in schedule_names:
            try:
                await self.resume_schedule(name)
            except Exception:  # noqa: PERF203
                continue

    async def bulk_delete_schedules(self, schedule_names: List[str]) -> None:
        """Delete multiple schedules in bulk"""
        for name in schedule_names:
            try:
                await self.delete_schedule(name)
            except Exception:  # noqa: PERF203
                continue

    async def validate_cron_expression(self, cron_expression: str, limit: int = 5) -> List[int]:
        """Validate a cron expression by getting its next execution times"""
        return await self.get_next_few_schedules(cron_expression, limit=limit)

    async def search_schedules_by_workflow(
        self, workflow_name: str, start: int = 0, size: int = 100
    ) -> SearchResultWorkflowScheduleExecutionModelAdapter:
        """Search schedules for a specific workflow"""
        return await self.search_schedules(
            start=start, size=size, query=f"workflowName:{workflow_name}"
        )

    async def search_schedules_by_status(
        self, paused: bool, start: int = 0, size: int = 100
    ) -> SearchResultWorkflowScheduleExecutionModelAdapter:
        """Search schedules by their status (paused/active)"""
        status_query = "paused:true" if paused else "paused:false"
        return await self.search_schedules(start=start, size=size, query=status_query)

    async def get_schedule_count(self) -> int:
        """Get the total number of schedules"""
        schedules = await self.get_all_schedules()
        return len(schedules)

    async def get_schedules_with_tag(self, tag_value: str) -> List[WorkflowScheduleModelAdapter]:
        """Get schedules that have a specific tag (alias for get_schedules_by_tag)"""
        return await self.get_schedules_by_tag(tag_value)
