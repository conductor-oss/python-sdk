from __future__ import annotations

from typing import List, Optional

from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import WorkflowScheduleModel
from conductor.client.http.models.save_schedule_request import SaveScheduleRequest
from conductor.client.http.models.search_result_workflow_schedule_execution_model import (
    SearchResultWorkflowScheduleExecutionModel,
)
from conductor.client.http.models.tag import Tag
from conductor.client.http.models.workflow_schedule import WorkflowSchedule
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.scheduler_client import SchedulerClient


class OrkesSchedulerClient(OrkesBaseClient, SchedulerClient):
    def __init__(self, configuration: Configuration):
        """Initialize the OrkesSchedulerClient with configuration.

        Args:
            configuration: Configuration object containing server settings and authentication

        Example:
            ```python
            from conductor.client.configuration.configuration import Configuration

            config = Configuration(server_api_url="http://localhost:8080/api")
            scheduler_client = OrkesSchedulerClient(config)
            ```
        """
        super().__init__(configuration)

    def save_schedule(self, save_schedule_request: SaveScheduleRequest, **kwargs) -> None:
        """Create or update a workflow schedule.

        Args:
            save_schedule_request: Schedule configuration including cron expression and workflow details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.save_schedule_request import SaveScheduleRequest
            from conductor.client.http.models.start_workflow_request import StartWorkflowRequest

            # Create a daily schedule at 9 AM
            start_request = StartWorkflowRequest(
                name="daily_report",
                version=1,
                input={"report_type": "daily"}
            )

            schedule_request = SaveScheduleRequest(
                name="daily_report_schedule",
                cron_expression="0 9 * * *",
                start_workflow_request=start_request,
                paused=False
            )

            scheduler_client.save_schedule(schedule_request)
            ```
        """
        self._scheduler_api.save_schedule(body=save_schedule_request, **kwargs)

    def get_schedule(self, name: str, **kwargs) -> WorkflowSchedule:
        """Get a workflow schedule by name.

        Args:
            name: Name of the schedule to retrieve
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowSchedule instance

        Example:
            ```python
            schedule = scheduler_client.get_schedule("daily_report_schedule")
            print(f"Schedule: {schedule.name}, Cron: {schedule.cron_expression}")
            ```
        """
        return self._scheduler_api.get_schedule(name=name, **kwargs)

    def get_all_schedules(
        self, workflow_name: Optional[str] = None, **kwargs
    ) -> List[WorkflowScheduleModel]:
        """Get all workflow schedules, optionally filtered by workflow name.

        Args:
            workflow_name: Optional workflow name to filter schedules
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowScheduleModel instances

        Example:
            ```python
            # Get all schedules
            all_schedules = scheduler_client.get_all_schedules()

            # Get schedules for a specific workflow
            report_schedules = scheduler_client.get_all_schedules("daily_report")
            ```
        """
        if workflow_name:
            kwargs.update({"workflow_name": workflow_name})
        return self._scheduler_api.get_all_schedules(**kwargs)

    def get_next_few_schedule_execution_times(
        self,
        cron_expression: str,
        schedule_start_time: Optional[int] = None,
        schedule_end_time: Optional[int] = None,
        limit: Optional[int] = None,
        **kwargs,
    ) -> List[int]:
        """Get the next few execution times for a cron expression.

        Args:
            cron_expression: Cron expression to evaluate
            schedule_start_time: Optional start time (epoch milliseconds)
            schedule_end_time: Optional end time (epoch milliseconds)
            limit: Optional maximum number of execution times to return
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of execution times as epoch milliseconds

        Example:
            ```python
            # Get next 5 executions for daily at 9 AM
            times = scheduler_client.get_next_few_schedule_execution_times(
                cron_expression="0 9 * * *",
                limit=5
            )

            for time in times:
                from datetime import datetime
                dt = datetime.fromtimestamp(time / 1000)
                print(f"Next execution: {dt}")
            ```
        """
        if schedule_start_time:
            kwargs.update({"schedule_start_time": schedule_start_time})
        if schedule_end_time:
            kwargs.update({"schedule_end_time": schedule_end_time})
        if limit:
            kwargs.update({"limit": limit})
        return self._scheduler_api.get_next_few_schedules(cron_expression=cron_expression, **kwargs)

    def delete_schedule(self, name: str, **kwargs) -> None:
        """Delete a workflow schedule.

        Args:
            name: Name of the schedule to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            scheduler_client.delete_schedule("old_schedule")
            ```
        """
        self._scheduler_api.delete_schedule(name=name, **kwargs)

    def pause_schedule(self, name: str, **kwargs) -> None:
        """Pause a workflow schedule.

        Args:
            name: Name of the schedule to pause
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            scheduler_client.pause_schedule("daily_report_schedule")
            ```
        """
        self._scheduler_api.pause_schedule(name=name, **kwargs)

    def pause_all_schedules(self, **kwargs) -> None:
        """Pause all workflow schedules.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Pause all schedules (e.g., during maintenance)
            scheduler_client.pause_all_schedules()
            ```
        """
        self._scheduler_api.pause_all_schedules(**kwargs)

    def resume_schedule(self, name: str, **kwargs) -> None:
        """Resume a paused workflow schedule.

        Args:
            name: Name of the schedule to resume
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            scheduler_client.resume_schedule("daily_report_schedule")
            ```
        """
        self._scheduler_api.resume_schedule(name=name, **kwargs)

    def resume_all_schedules(self, **kwargs) -> None:
        """Resume all paused workflow schedules.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Resume all schedules (e.g., after maintenance)
            scheduler_client.resume_all_schedules()
            ```
        """
        self._scheduler_api.resume_all_schedules(**kwargs)

    def search_schedule_executions(
        self,
        start: Optional[int] = None,
        size: Optional[int] = None,
        sort: Optional[str] = None,
        free_text: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs,
    ) -> SearchResultWorkflowScheduleExecutionModel:
        """Search workflow schedule executions.

        Args:
            start: Start index for pagination
            size: Number of results to return
            sort: Sort order (e.g., "startTime:DESC")
            free_text: Free text search query
            query: Structured query string
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            SearchResultWorkflowScheduleExecutionModel with execution results

        Example:
            ```python
            # Search recent executions
            results = scheduler_client.search_schedule_executions(
                start=0,
                size=20,
                sort="startTime:DESC"
            )

            print(f"Total executions: {results.total_hits}")
            for execution in results.results:
                print(f"Execution: {execution.workflow_id}, Status: {execution.state}")
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
        return self._scheduler_api.search_v2(**kwargs)

    def requeue_all_execution_records(self, **kwargs) -> None:
        """Requeue all pending schedule execution records.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Requeue failed executions
            scheduler_client.requeue_all_execution_records()
            ```
        """
        self._scheduler_api.requeue_all_execution_records(**kwargs)

    @deprecated("set_scheduler_tags is deprecated; use set_scheduler_tags_validated instead")
    @typing_deprecated("set_scheduler_tags is deprecated; use set_scheduler_tags_validated instead")
    def set_scheduler_tags(self, tags: List[MetadataTag], name: str, **kwargs) -> None:
        """Set tags for a schedule.

        .. deprecated::
            Use set_scheduler_tags_validated() instead.

        Args:
            tags: List of tags to set
            name: Name of the schedule
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None
        """
        self._scheduler_api.put_tag_for_schedule(tags, name, **kwargs)

    def set_scheduler_tags_validated(self, tags: List[Tag], name: str, **kwargs) -> None:
        """Set tags for a schedule.

        Args:
            tags: List of tags to set
            name: Name of the schedule
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.tag import Tag

            tags = [
                Tag(key="environment", value="production"),
                Tag(key="frequency", value="daily")
            ]
            scheduler_client.set_scheduler_tags_validated(tags, "daily_report_schedule")
            ```
        """
        self._scheduler_api.put_tag_for_schedule(body=tags, name=name, **kwargs)

    def get_scheduler_tags(self, name: str, **kwargs) -> List[Tag]:
        """Get tags for a schedule.

        Args:
            name: Name of the schedule
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of Tag instances

        Example:
            ```python
            tags = scheduler_client.get_scheduler_tags("daily_report_schedule")
            for tag in tags:
                print(f"Tag: {tag.key}={tag.value}")
            ```
        """
        return self._scheduler_api.get_tags_for_schedule(name=name, **kwargs)

    @deprecated("delete_scheduler_tags is deprecated; use delete_scheduler_tags_validated instead")
    @typing_deprecated(
        "delete_scheduler_tags is deprecated; use delete_scheduler_tags_validated instead"
    )
    def delete_scheduler_tags(self, tags: List[MetadataTag], name: str, **kwargs) -> None:
        """Delete tags for a schedule.

        .. deprecated::
            Use delete_scheduler_tags_validated() instead.

        Args:
            tags: List of tags to delete
            name: Name of the schedule
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None
        """
        return self._scheduler_api.delete_tag_for_schedule(tags, name)

    def delete_scheduler_tags_validated(self, tags: List[Tag], name: str, **kwargs) -> None:
        """Delete tags for a schedule.

        Args:
            tags: List of tags to delete
            name: Name of the schedule
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.tag import Tag

            tags_to_delete = [Tag(key="environment", value="staging")]
            scheduler_client.delete_scheduler_tags_validated(tags_to_delete, "daily_report_schedule")
            ```
        """
        self._scheduler_api.delete_tag_for_schedule(body=tags, name=name, **kwargs)

    def get_schedules_by_tag(self, tag: str, **kwargs) -> List[WorkflowScheduleModel]:
        """Get all schedules with a specific tag.

        Args:
            tag: Tag to filter by (format: "key:value")
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowScheduleModel instances

        Example:
            ```python
            # Get all production schedules
            prod_schedules = scheduler_client.get_schedules_by_tag("environment:production")
            for schedule in prod_schedules:
                print(f"Schedule: {schedule.name}")
            ```
        """
        return self._scheduler_api.get_schedules_by_tag(tag=tag, **kwargs)
