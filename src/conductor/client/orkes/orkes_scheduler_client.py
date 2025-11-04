from __future__ import annotations

from typing import List, Optional

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import WorkflowScheduleModel
from conductor.client.http.models.save_schedule_request import SaveScheduleRequest
from conductor.client.http.models.search_result_workflow_schedule_execution_model import (
    SearchResultWorkflowScheduleExecutionModel,
)
from conductor.client.http.models.workflow_schedule import WorkflowSchedule
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.http.models.tag import Tag
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.scheduler_client import SchedulerClient
from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated


class OrkesSchedulerClient(OrkesBaseClient, SchedulerClient):
    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def save_schedule(self, save_schedule_request: SaveScheduleRequest, **kwargs) -> None:
        self._scheduler_api.save_schedule(body=save_schedule_request, **kwargs)

    def get_schedule(self, name: str, **kwargs) -> WorkflowSchedule:
        return self._scheduler_api.get_schedule(name=name, **kwargs)

    def get_all_schedules(
        self, workflow_name: Optional[str] = None, **kwargs
    ) -> List[WorkflowScheduleModel]:
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
        if schedule_start_time:
            kwargs.update({"schedule_start_time": schedule_start_time})
        if schedule_end_time:
            kwargs.update({"schedule_end_time": schedule_end_time})
        if limit:
            kwargs.update({"limit": limit})
        return self._scheduler_api.get_next_few_schedules(cron_expression=cron_expression, **kwargs)

    def delete_schedule(self, name: str, **kwargs) -> None:
        self._scheduler_api.delete_schedule(name=name, **kwargs)

    def pause_schedule(self, name: str, **kwargs) -> None:
        self._scheduler_api.pause_schedule(name=name, **kwargs)

    def pause_all_schedules(self, **kwargs) -> None:
        self._scheduler_api.pause_all_schedules(**kwargs)

    def resume_schedule(self, name: str, **kwargs) -> None:
        self._scheduler_api.resume_schedule(name=name, **kwargs)

    def resume_all_schedules(self, **kwargs) -> None:
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
        self._scheduler_api.requeue_all_execution_records(**kwargs)

    @deprecated("set_scheduler_tags is deprecated; use set_scheduler_tags_validated instead")
    @typing_deprecated("set_scheduler_tags is deprecated; use set_scheduler_tags_validated instead")
    def set_scheduler_tags(self, tags: List[MetadataTag], name: str, **kwargs) -> None:
        self._scheduler_api.put_tag_for_schedule(tags, name, **kwargs)

    def set_scheduler_tags_validated(self, tags: List[Tag], name: str, **kwargs) -> None:
        self._scheduler_api.put_tag_for_schedule(body=tags, name=name, **kwargs)

    def get_scheduler_tags(self, name: str, **kwargs) -> List[Tag]:
        return self._scheduler_api.get_tags_for_schedule(name=name, **kwargs)

    @deprecated("delete_scheduler_tags is deprecated; use delete_scheduler_tags_validated instead")
    @typing_deprecated(
        "delete_scheduler_tags is deprecated; use delete_scheduler_tags_validated instead"
    )
    def delete_scheduler_tags(self, tags: List[MetadataTag], name: str, **kwargs) -> None:
        return self._scheduler_api.delete_tag_for_schedule(tags, name)

    def delete_scheduler_tags_validated(self, tags: List[Tag], name: str, **kwargs) -> None:
        self._scheduler_api.delete_tag_for_schedule(body=tags, name=name, **kwargs)

    def get_schedules_by_tag(self, tag: str, **kwargs) -> List[WorkflowScheduleModel]:
        return self._scheduler_api.get_schedules_by_tag(tag=tag, **kwargs)
