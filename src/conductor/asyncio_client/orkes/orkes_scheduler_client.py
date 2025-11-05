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
        """Initialize the OrkesSchedulerClient with configuration and API client.

        Args:
            configuration: Configuration object containing server settings and authentication
            api_client: ApiClient instance for making API requests

        Example:
            ```python
            from conductor.asyncio_client.configuration.configuration import Configuration
            from conductor.asyncio_client.adapters import ApiClient

            config = Configuration(server_api_url="http://localhost:8080/api")
            api_client = ApiClient(configuration=config)
            scheduler_client = OrkesSchedulerClient(config, api_client)
            ```
        """
        super().__init__(configuration, api_client)

    # Core Schedule Operations
    @deprecated("save_schedule is deprecated; use save_schedule_validated instead")
    @typing_deprecated("save_schedule is deprecated; use save_schedule_validated instead")
    async def save_schedule(self, save_schedule_request: SaveScheduleRequestAdapter) -> object:
        """Create or update a schedule for a specified workflow.

        .. deprecated::
            Use save_schedule_validated instead for type-safe validated responses.

        Args:
            save_schedule_request: Complete schedule configuration

        Returns:
            Raw response object from the API

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.save_schedule_request_adapter import SaveScheduleRequestAdapter

            schedule = SaveScheduleRequestAdapter(
                name="daily_report",
                cron_expression="0 9 * * *",
                start_workflow_request=start_request
            )
            await scheduler_client.save_schedule(schedule)
            ```
        """
        return await self._scheduler_api.save_schedule(save_schedule_request)

    async def save_schedule_validated(
        self, save_schedule_request: SaveScheduleRequestAdapter, **kwargs
    ) -> None:
        """Create or update a schedule for a specified workflow.

        Args:
            save_schedule_request: Complete schedule configuration
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.save_schedule_request_adapter import SaveScheduleRequestAdapter
            from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import StartWorkflowRequestAdapter

            start_request = StartWorkflowRequestAdapter(
                name="daily_report_workflow",
                input={"date": "today"}
            )
            schedule = SaveScheduleRequestAdapter(
                name="daily_report",
                cron_expression="0 9 * * *",  # Every day at 9 AM
                start_workflow_request=start_request,
                timezone="America/New_York"
            )
            await scheduler_client.save_schedule_validated(schedule)
            ```
        """
        await self._scheduler_api.save_schedule(
            save_schedule_request=save_schedule_request, **kwargs
        )

    async def get_schedule(self, name: str, **kwargs) -> WorkflowScheduleAdapter:
        """Get a workflow schedule by name.

        Args:
            name: Name of the schedule to retrieve
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowScheduleAdapter instance containing the schedule details

        Example:
            ```python
            schedule = await scheduler_client.get_schedule("daily_report")
            print(f"Cron: {schedule.cron_expression}")
            print(f"Paused: {schedule.paused}")
            ```
        """
        return await self._scheduler_api.get_schedule(name=name, **kwargs)

    @deprecated("delete_schedule is deprecated; use delete_schedule_validated instead")
    @typing_deprecated("delete_schedule is deprecated; use delete_schedule_validated instead")
    async def delete_schedule(self, name: str) -> object:
        """Delete an existing workflow schedule by name.

        .. deprecated::
            Use delete_schedule_validated instead for type-safe validated responses.

        Args:
            name: Name of the schedule to delete

        Returns:
            Raw response object from the API

        Example:
            ```python
            await scheduler_client.delete_schedule("old_daily_report")
            ```
        """
        return await self._scheduler_api.delete_schedule(name)

    async def delete_schedule_validated(self, name: str, **kwargs) -> None:
        """Delete an existing workflow schedule by name.

        Args:
            name: Name of the schedule to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await scheduler_client.delete_schedule_validated("old_daily_report")
            ```
        """
        await self._scheduler_api.delete_schedule(name=name, **kwargs)

    async def get_all_schedules(
        self, workflow_name: Optional[str] = None, **kwargs
    ) -> List[WorkflowScheduleModelAdapter]:
        """Get all workflow schedules, optionally filtered by workflow name.

        Args:
            workflow_name: Optional workflow name to filter schedules
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowScheduleModelAdapter instances

        Example:
            ```python
            # Get all schedules
            all_schedules = await scheduler_client.get_all_schedules()

            # Get schedules for a specific workflow
            report_schedules = await scheduler_client.get_all_schedules("daily_report_workflow")
            for schedule in report_schedules:
                print(f"Schedule: {schedule.name}, Cron: {schedule.cron_expression}")
            ```
        """
        return await self._scheduler_api.get_all_schedules(workflow_name=workflow_name, **kwargs)

    # Schedule Control Operations
    @deprecated("pause_schedule is deprecated; use pause_schedule_validated instead")
    @typing_deprecated("pause_schedule is deprecated; use pause_schedule_validated instead")
    async def pause_schedule(self, name: str) -> object:
        """Pause a workflow schedule.

        .. deprecated::
            Use pause_schedule_validated instead for type-safe validated responses.

        Args:
            name: Name of the schedule to pause

        Returns:
            Raw response object from the API

        Example:
            ```python
            await scheduler_client.pause_schedule("daily_report")
            ```
        """
        return await self._scheduler_api.pause_schedule(name)

    async def pause_schedule_validated(self, name: str, **kwargs) -> None:
        """Pause a workflow schedule.

        Args:
            name: Name of the schedule to pause
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Pause a schedule temporarily
            await scheduler_client.pause_schedule_validated("daily_report")
            ```
        """
        await self._scheduler_api.pause_schedule(name=name, **kwargs)

    @deprecated("resume_schedule is deprecated; use resume_schedule_validated instead")
    @typing_deprecated("resume_schedule is deprecated; use resume_schedule_validated instead")
    async def resume_schedule(self, name: str) -> object:
        """Resume a paused workflow schedule.

        .. deprecated::
            Use resume_schedule_validated instead for type-safe validated responses.

        Args:
            name: Name of the schedule to resume

        Returns:
            Raw response object from the API

        Example:
            ```python
            await scheduler_client.resume_schedule("daily_report")
            ```
        """
        return await self._scheduler_api.resume_schedule(name)

    async def resume_schedule_validated(self, name: str, **kwargs) -> None:
        """Resume a paused workflow schedule.

        Args:
            name: Name of the schedule to resume
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Resume a paused schedule
            await scheduler_client.resume_schedule_validated("daily_report")
            ```
        """
        await self._scheduler_api.resume_schedule(name=name, **kwargs)

    @deprecated("pause_all_schedules is deprecated; use pause_all_schedules_validated instead")
    @typing_deprecated(
        "pause_all_schedules is deprecated; use pause_all_schedules_validated instead"
    )
    async def pause_all_schedules(self) -> Dict[str, object]:
        """Pause all workflow schedules.

        .. deprecated::
            Use pause_all_schedules_validated instead for type-safe validated responses.

        Returns:
            Dictionary with pause operation results

        Example:
            ```python
            await scheduler_client.pause_all_schedules()
            ```
        """
        return await self._scheduler_api.pause_all_schedules()

    async def pause_all_schedules_validated(self, **kwargs) -> None:
        """Pause all workflow schedules.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Pause all schedules for maintenance
            await scheduler_client.pause_all_schedules_validated()
            ```
        """
        await self._scheduler_api.pause_all_schedules(**kwargs)

    @deprecated("resume_all_schedules is deprecated; use resume_all_schedules_validated instead")
    @typing_deprecated(
        "resume_all_schedules is deprecated; use resume_all_schedules_validated instead"
    )
    async def resume_all_schedules(self, **kwargs) -> Dict[str, object]:
        """Resume all paused workflow schedules.

        .. deprecated::
            Use resume_all_schedules_validated instead for type-safe validated responses.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary with resume operation results

        Example:
            ```python
            await scheduler_client.resume_all_schedules()
            ```
        """
        return await self._scheduler_api.resume_all_schedules(**kwargs)

    async def resume_all_schedules_validated(self, **kwargs) -> None:
        """Resume all paused workflow schedules.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Resume all schedules after maintenance
            await scheduler_client.resume_all_schedules_validated()
            ```
        """
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
        """Search for workflow schedules with advanced filtering.

        .. deprecated::
            Use search_schedule_executions instead for consistent API interface.

        Args:
            start: Starting index for pagination (default: 0)
            size: Number of results to return (default: 100)
            sort: Sort order specification
            free_text: Free text search query
            query: Structured query string
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            SearchResultWorkflowScheduleExecutionModelAdapter with matching schedules

        Example:
            ```python
            results = await scheduler_client.search_schedules(
                start=0,
                size=50,
                query="workflowName:daily_report"
            )
            ```
        """
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
        **kwargs,
    ) -> SearchResultWorkflowScheduleExecutionModelAdapter:
        """Search for workflow schedule executions with advanced filtering.

        Args:
            start: Starting index for pagination
            size: Number of results to return
            sort: Sort order specification
            free_text: Free text search query
            query: Structured query string (e.g., "workflowName:my_workflow")
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            SearchResultWorkflowScheduleExecutionModelAdapter with matching schedule executions

        Example:
            ```python
            # Search for schedules by workflow name
            results = await scheduler_client.search_schedule_executions(
                start=0,
                size=50,
                query="workflowName:daily_report"
            )
            print(f"Found {results.total_hits} schedules")

            # Free text search
            results = await scheduler_client.search_schedule_executions(
                free_text="daily report"
            )
            ```
        """
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
        """Get schedules filtered by tag value.

        Args:
            tag_value: Tag value to filter by
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowScheduleModelAdapter instances with matching tag

        Example:
            ```python
            # Get all schedules with specific tag
            schedules = await scheduler_client.get_schedules_by_tag("production")
            for schedule in schedules:
                print(f"Schedule: {schedule.name}")
            ```
        """
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
        """Get the next execution times for a cron expression.

        .. deprecated::
            Use get_next_few_schedule_execution_times instead.

        Args:
            cron_expression: Cron expression to evaluate
            schedule_start_time: Optional start time (epoch milliseconds)
            schedule_end_time: Optional end time (epoch milliseconds)
            limit: Maximum number of execution times to return
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of execution times as epoch milliseconds

        Example:
            ```python
            times = await scheduler_client.get_next_few_schedules("0 9 * * *", limit=5)
            ```
        """
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
        """Add tags to a workflow schedule.

        .. deprecated::
            Use set_tags_for_schedule instead.

        Args:
            name: Name of the schedule
            tags: List of tags to add
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [TagAdapter(key="environment", value="production")]
            await scheduler_client.put_tag_for_schedule("daily_report", tags)
            ```
        """
        await self._scheduler_api.put_tag_for_schedule(name=name, tag=tags, **kwargs)

    async def set_tags_for_schedule(self, name: str, tags: List[TagAdapter], **kwargs) -> None:
        """Set tags for a workflow schedule.

        Args:
            name: Name of the schedule
            tags: List of tags to set
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [
                TagAdapter(key="environment", value="production"),
                TagAdapter(key="team", value="data")
            ]
            await scheduler_client.set_tags_for_schedule("daily_report", tags)
            ```
        """
        await self._scheduler_api.put_tag_for_schedule(name=name, tag=tags, **kwargs)

    @deprecated("get_tags_for_schedule is deprecated; use get_scheduler_tags instead")
    @typing_deprecated("get_tags_for_schedule is deprecated; use get_scheduler_tags instead")
    async def get_tags_for_schedule(self, name: str, **kwargs) -> List[TagAdapter]:
        """Get tags associated with a workflow schedule.

        .. deprecated::
            Use get_scheduler_tags instead.

        Args:
            name: Name of the schedule
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TagAdapter instances

        Example:
            ```python
            tags = await scheduler_client.get_tags_for_schedule("daily_report")
            ```
        """
        return await self._scheduler_api.get_tags_for_schedule(name, **kwargs)

    async def get_scheduler_tags(self, name: str, **kwargs) -> List[TagAdapter]:
        """Get tags associated with a workflow schedule.

        Args:
            name: Name of the schedule
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TagAdapter instances

        Example:
            ```python
            tags = await scheduler_client.get_scheduler_tags("daily_report")
            for tag in tags:
                print(f"{tag.key}: {tag.value}")
            ```
        """
        return await self._scheduler_api.get_tags_for_schedule(name=name, **kwargs)

    @deprecated("delete_tag_for_schedule is deprecated; use delete_scheduler_tags instead")
    @typing_deprecated("delete_tag_for_schedule is deprecated; use delete_scheduler_tags instead")
    async def delete_tag_for_schedule(self, name: str, tags: List[TagAdapter], **kwargs) -> None:
        """Delete specific tags from a workflow schedule.

        .. deprecated::
            Use delete_scheduler_tags instead.

        Args:
            name: Name of the schedule
            tags: List of tags to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [TagAdapter(key="environment", value="production")]
            await scheduler_client.delete_tag_for_schedule("daily_report", tags)
            ```
        """
        await self._scheduler_api.delete_tag_for_schedule(name, tags, **kwargs)

    async def delete_scheduler_tags(self, tags: List[TagAdapter], name: str, **kwargs) -> None:
        """Delete specific tags from a workflow schedule.

        Args:
            tags: List of tags to delete
            name: Name of the schedule
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [TagAdapter(key="environment", value="production")]
            await scheduler_client.delete_scheduler_tags(tags, "daily_report")
            ```
        """
        await self._scheduler_api.delete_tag_for_schedule(name=name, tag=tags, **kwargs)

    # Schedule Execution Management
    @deprecated(
        "requeue_all_execution_records is deprecated; use requeue_all_execution_records_validated instead"
    )
    @typing_deprecated(
        "requeue_all_execution_records is deprecated; use requeue_all_execution_records_validated instead"
    )
    async def requeue_all_execution_records(self) -> Dict[str, object]:
        """Requeue all execution records for scheduled workflows.

        .. deprecated::
            Use requeue_all_execution_records_validated instead for type-safe validated responses.

        Returns:
            Dictionary with requeue operation results

        Example:
            ```python
            await scheduler_client.requeue_all_execution_records()
            ```
        """
        return await self._scheduler_api.requeue_all_execution_records()

    async def requeue_all_execution_records_validated(self, **kwargs) -> None:
        """Requeue all execution records for scheduled workflows.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await scheduler_client.requeue_all_execution_records_validated()
            ```
        """
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
        """Create a new workflow schedule with simplified parameters.

        .. deprecated::
            Use create_schedule_validated instead for type-safe validated responses.

        Args:
            name: Unique name for the schedule
            cron_expression: Cron expression defining when to run (e.g., "0 9 * * *" for daily at 9 AM)
            workflow_name: Name of the workflow to execute
            workflow_version: Optional workflow version. If None, uses latest version
            start_workflow_request: Optional dict with workflow input parameters
            timezone: Optional timezone (e.g., "America/New_York"). If None, uses UTC
            run_catch_up: If True, runs missed executions when schedule is resumed

        Returns:
            Raw response object from the API

        Example:
            ```python
            await scheduler_client.create_schedule(
                name="daily_report",
                cron_expression="0 9 * * *",
                workflow_name="generate_report",
                timezone="America/New_York",
                start_workflow_request={"input": {"date": "today"}}
            )
            ```
        """

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
        """Create a new workflow schedule with simplified parameters.

        Convenience method that simplifies schedule creation by accepting basic parameters
        instead of requiring full adapter objects.

        Args:
            name: Unique name for the schedule
            cron_expression: Cron expression defining when to run (e.g., "0 9 * * *" for daily at 9 AM)
            workflow_name: Name of the workflow to execute
            workflow_version: Optional workflow version. If None, uses latest version
            start_workflow_request: Optional dict with workflow parameters (input, correlationId, priority, taskToDomain)
            timezone: Optional timezone (e.g., "America/New_York"). If None, uses UTC
            run_catch_up: If True, runs missed executions when schedule is resumed
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Create a daily report schedule
            await scheduler_client.create_schedule_validated(
                name="daily_report",
                cron_expression="0 9 * * MON-FRI",  # Weekdays at 9 AM
                workflow_name="generate_report",
                workflow_version=1,
                timezone="America/New_York",
                start_workflow_request={
                    "input": {"report_type": "daily", "format": "pdf"},
                    "priority": 5
                }
            )

            # Create a simple hourly schedule
            await scheduler_client.create_schedule_validated(
                name="hourly_sync",
                cron_expression="0 * * * *",  # Every hour
                workflow_name="data_sync"
            )
            ```
        """
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
        """Update an existing schedule with new parameters.

        .. deprecated::
            Use update_schedule_validated instead for type-safe validated responses.

        Args:
            name: Name of the schedule to update
            cron_expression: Optional new cron expression
            paused: Optional paused status
            run_catch_up: Optional run catch-up setting
            timezone: Optional new timezone
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Raw response object from the API

        Example:
            ```python
            # Update schedule to run every 2 hours instead
            await scheduler_client.update_schedule(
                "daily_report",
                cron_expression="0 */2 * * *"
            )
            ```
        """
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
        """Update an existing schedule with new parameters.

        Fetches the existing schedule and updates only the specified fields,
        preserving all other settings.

        Args:
            name: Name of the schedule to update
            cron_expression: Optional new cron expression
            paused: Optional paused status
            run_catch_up: Optional run catch-up setting
            timezone: Optional new timezone
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Update schedule to run every 2 hours
            await scheduler_client.update_schedule_validated(
                "daily_report",
                cron_expression="0 */2 * * *"
            )

            # Pause a schedule
            await scheduler_client.update_schedule_validated(
                "daily_report",
                paused=True
            )

            # Change timezone
            await scheduler_client.update_schedule_validated(
                "daily_report",
                timezone="Europe/London"
            )
            ```
        """
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
        """Check if a schedule exists.

        Args:
            name: Name of the schedule to check
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            True if schedule exists, False otherwise

        Example:
            ```python
            if await scheduler_client.schedule_exists("daily_report"):
                print("Schedule exists")
            else:
                print("Schedule not found")
            ```
        """
        try:
            await self.get_schedule(name=name, **kwargs)
            return True
        except Exception:
            return False

    async def get_schedules_by_workflow(
        self, workflow_name: str, **kwargs
    ) -> List[WorkflowScheduleModelAdapter]:
        """Get all schedules for a specific workflow.

        Args:
            workflow_name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowScheduleModelAdapter instances

        Example:
            ```python
            schedules = await scheduler_client.get_schedules_by_workflow("generate_report")
            print(f"Found {len(schedules)} schedules for this workflow")
            ```
        """
        return await self.get_all_schedules(workflow_name=workflow_name, **kwargs)

    async def get_active_schedules(self, **kwargs) -> List[WorkflowScheduleModelAdapter]:
        """Get all active (non-paused) schedules.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of active WorkflowScheduleModelAdapter instances

        Example:
            ```python
            active = await scheduler_client.get_active_schedules()
            print(f"{len(active)} schedules are currently running")
            ```
        """
        all_schedules = await self.get_all_schedules(**kwargs)
        return [schedule for schedule in all_schedules if not schedule.paused]

    async def get_paused_schedules(self, **kwargs) -> List[WorkflowScheduleModelAdapter]:
        """Get all paused schedules.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of paused WorkflowScheduleModelAdapter instances

        Example:
            ```python
            paused = await scheduler_client.get_paused_schedules()
            print(f"{len(paused)} schedules are paused")
            ```
        """
        all_schedules = await self.get_all_schedules(**kwargs)
        return [schedule for schedule in all_schedules if schedule.paused]

    async def bulk_pause_schedules(self, schedule_names: List[str], **kwargs) -> None:
        """Pause multiple schedules in bulk.

        Continues even if some pause operations fail.

        Args:
            schedule_names: List of schedule names to pause
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            schedules = ["schedule1", "schedule2", "schedule3"]
            await scheduler_client.bulk_pause_schedules(schedules)
            ```
        """
        for name in schedule_names:
            try:
                await self.pause_schedule_validated(name=name, **kwargs)
            except Exception:  # noqa: PERF203
                continue

    async def bulk_resume_schedules(self, schedule_names: List[str], **kwargs) -> None:
        """Resume multiple schedules in bulk.

        Continues even if some resume operations fail.

        Args:
            schedule_names: List of schedule names to resume
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            schedules = ["schedule1", "schedule2", "schedule3"]
            await scheduler_client.bulk_resume_schedules(schedules)
            ```
        """
        for name in schedule_names:
            try:
                await self.resume_schedule_validated(name=name, **kwargs)
            except Exception:  # noqa: PERF203
                continue

    async def bulk_delete_schedules(self, schedule_names: List[str], **kwargs) -> None:
        """Delete multiple schedules in bulk.

        Continues even if some delete operations fail.

        Args:
            schedule_names: List of schedule names to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            old_schedules = ["old_schedule1", "old_schedule2"]
            await scheduler_client.bulk_delete_schedules(old_schedules)
            ```
        """
        for name in schedule_names:
            try:
                await self.delete_schedule_validated(name=name, **kwargs)
            except Exception:  # noqa: PERF203
                continue

    async def validate_cron_expression(
        self, cron_expression: str, limit: int = 5, **kwargs
    ) -> List[int]:
        """Validate a cron expression by getting its next execution times.

        Args:
            cron_expression: Cron expression to validate
            limit: Number of execution times to return (default: 5)
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of next execution times as epoch milliseconds

        Example:
            ```python
            # Validate a cron expression and see when it will run
            times = await scheduler_client.validate_cron_expression("0 9 * * MON-FRI")
            from datetime import datetime
            for timestamp in times:
                dt = datetime.fromtimestamp(timestamp / 1000)
                print(f"Will run at: {dt}")
            ```
        """
        return await self.get_next_few_schedule_execution_times(
            cron_expression=cron_expression, limit=limit, **kwargs
        )

    async def search_schedules_by_workflow(
        self, workflow_name: str, start: int = 0, size: int = 100, **kwargs
    ) -> SearchResultWorkflowScheduleExecutionModelAdapter:
        """Search schedules for a specific workflow.

        Args:
            workflow_name: Name of the workflow to search for
            start: Starting index for pagination (default: 0)
            size: Number of results to return (default: 100)
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            SearchResultWorkflowScheduleExecutionModelAdapter with matching schedules

        Example:
            ```python
            results = await scheduler_client.search_schedules_by_workflow("generate_report")
            print(f"Found {results.total_hits} schedules")
            ```
        """
        return await self.search_schedule_executions(
            start=start, size=size, query=f"workflowName:{workflow_name}", **kwargs
        )

    async def search_schedules_by_status(
        self, paused: bool, start: int = 0, size: int = 100, **kwargs
    ) -> SearchResultWorkflowScheduleExecutionModelAdapter:
        """Search schedules by their status (paused/active).

        Args:
            paused: If True, search for paused schedules. If False, search for active schedules
            start: Starting index for pagination (default: 0)
            size: Number of results to return (default: 100)
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            SearchResultWorkflowScheduleExecutionModelAdapter with matching schedules

        Example:
            ```python
            # Get all paused schedules
            paused_results = await scheduler_client.search_schedules_by_status(paused=True)

            # Get all active schedules
            active_results = await scheduler_client.search_schedules_by_status(paused=False)
            ```
        """
        status_query = "paused:true" if paused else "paused:false"
        return await self.search_schedule_executions(
            start=start, size=size, query=status_query, **kwargs
        )

    async def get_schedule_count(self, **kwargs) -> int:
        """Get the total number of schedules.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Total count of schedules as integer

        Example:
            ```python
            count = await scheduler_client.get_schedule_count()
            print(f"Total schedules: {count}")
            ```
        """
        schedules = await self.get_all_schedules(**kwargs)
        return len(schedules)

    async def get_schedules_with_tag(
        self, tag_value: str, **kwargs
    ) -> List[WorkflowScheduleModelAdapter]:
        """Get schedules that have a specific tag (alias for get_schedules_by_tag).

        Args:
            tag_value: Tag value to filter by
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowScheduleModelAdapter instances with matching tag

        Example:
            ```python
            schedules = await scheduler_client.get_schedules_with_tag("production")
            ```
        """
        return await self.get_schedules_by_tag(tag_value=tag_value, **kwargs)

    async def get_next_few_schedule_execution_times(
        self,
        cron_expression: str,
        schedule_start_time: Optional[int] = None,
        schedule_end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[int]:
        """Get the next few execution times for a cron expression.

        Useful for validating cron expressions and previewing when schedules will run.

        Args:
            cron_expression: Cron expression to evaluate
            schedule_start_time: Optional start time in epoch milliseconds
            schedule_end_time: Optional end time in epoch milliseconds
            limit: Maximum number of execution times to return

        Returns:
            List of execution times as epoch milliseconds

        Example:
            ```python
            from datetime import datetime

            # Get next 10 execution times for daily 9 AM schedule
            times = await scheduler_client.get_next_few_schedule_execution_times(
                cron_expression="0 9 * * *",
                limit=10
            )

            # Display the times
            for timestamp in times:
                dt = datetime.fromtimestamp(timestamp / 1000)
                print(f"Will execute at: {dt}")

            # Get executions within a time window
            import time
            start = int(time.time() * 1000)  # Now
            end = start + (7 * 24 * 60 * 60 * 1000)  # 7 days from now
            times = await scheduler_client.get_next_few_schedule_execution_times(
                cron_expression="0 */6 * * *",  # Every 6 hours
                schedule_start_time=start,
                schedule_end_time=end
            )
            ```
        """
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
