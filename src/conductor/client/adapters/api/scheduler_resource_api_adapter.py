from conductor.client.codegen.api.scheduler_resource_api import SchedulerResourceApi
from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from typing import List, Dict
from conductor.client.http.models.tag import Tag
from conductor.client.http.models.workflow_schedule_model import WorkflowScheduleModel
from conductor.client.http.models.workflow_schedule import WorkflowSchedule
from conductor.client.http.models.save_schedule_request import SaveScheduleRequest
from conductor.client.http.models.search_result_workflow_schedule_execution_model import (
    SearchResultWorkflowScheduleExecutionModel,
)


class SchedulerResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = SchedulerResourceApi(api_client)

    def delete_schedule(self, name: str, **kwargs) -> object:
        """Delete a schedule"""
        return self._api.delete_schedule(name, **kwargs)

    def delete_tag_for_schedule(self, body: List[Tag], name: str, **kwargs) -> None:
        """Delete a tag for a schedule"""
        return self._api.delete_tag_for_schedule(body, name, **kwargs)

    def get_all_schedules(self, **kwargs) -> List[WorkflowScheduleModel]:
        """Get all schedules"""
        return self._api.get_all_schedules(**kwargs)

    def get_next_few_schedules(self, cron_expression: str, **kwargs) -> List[int]:
        """Get the next few schedules"""
        return self._api.get_next_few_schedules(cron_expression, **kwargs)

    def get_schedule(self, name: str, **kwargs) -> WorkflowSchedule:
        """Get a schedule"""
        return self._api.get_schedule(name, **kwargs)

    def get_schedules_by_tag(self, tag: str, **kwargs) -> List[WorkflowScheduleModel]:
        """Get schedules by tag"""
        return self._api.get_schedules_by_tag(tag, **kwargs)

    def get_tags_for_schedule(self, name: str, **kwargs) -> List[Tag]:
        """Get tags for a schedule"""
        return self._api.get_tags_for_schedule(name, **kwargs)

    def pause_all_schedules(self, **kwargs) -> Dict[str, object]:
        """Pause all schedules"""
        return self._api.pause_all_schedules(**kwargs)

    def pause_schedule(self, name: str, **kwargs) -> object:
        """Pause a schedule"""
        return self._api.pause_schedule(name, **kwargs)

    def put_tag_for_schedule(self, body: List[Tag], name: str, **kwargs) -> None:
        """Put a tag for a schedule"""
        return self._api.put_tag_for_schedule(body, name, **kwargs)

    def requeue_all_execution_records(self, **kwargs) -> Dict[str, object]:
        """Requeue all execution records"""
        return self._api.requeue_all_execution_records(**kwargs)

    def resume_all_schedules(self, **kwargs) -> Dict[str, object]:
        """Resume all schedules"""
        return self._api.resume_all_schedules(**kwargs)

    def resume_schedule(self, name: str, **kwargs) -> object:
        """Resume a schedule"""
        return self._api.resume_schedule(name, **kwargs)

    def save_schedule(self, body: SaveScheduleRequest, **kwargs) -> object:
        """Save a schedule"""
        return self._api.save_schedule(body, **kwargs)

    def search_v2(self, **kwargs) -> SearchResultWorkflowScheduleExecutionModel:
        """Search for workflows based on payload and other parameters"""
        return self._api.search_v2(**kwargs)
