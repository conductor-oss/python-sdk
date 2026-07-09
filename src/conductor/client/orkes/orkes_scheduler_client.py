from __future__ import annotations
from typing import Optional, List

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.save_schedule_request import SaveScheduleRequest
from conductor.client.http.models.search_result_workflow_schedule_execution_model import \
    SearchResultWorkflowScheduleExecutionModel
from conductor.client.http.models.workflow_schedule import WorkflowSchedule
from conductor.client.http.rest import ApiException
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.scheduler_client import SchedulerClient


class OrkesSchedulerClient(OrkesBaseClient, SchedulerClient):
    def __init__(self, configuration: Configuration):
        super(OrkesSchedulerClient, self).__init__(configuration)
        # Per-schedule pause/resume verbs differ by server family: OSS Conductor maps them
        # PUT-only, Orkes Conductor GET-only. We send PUT first and remember a 405 so
        # subsequent calls go straight to the legacy GET dialect.
        self._legacy_scheduler_verbs = False

    def save_schedule(self, save_schedule_request: SaveScheduleRequest):
        self.schedulerResourceApi.save_schedule(save_schedule_request)

    def get_schedule(self, name: str) -> Optional[WorkflowSchedule]:
        schedule = self.schedulerResourceApi.get_schedule(name)
        # Conductor returns 200 with an empty/null body for missing schedules, which
        # deserializes to an empty model. A real schedule always carries `name`.
        if not schedule or not getattr(schedule, "name", None):
            return None
        return schedule

    def get_all_schedules(self, workflow_name: Optional[str] = None) -> List[WorkflowSchedule]:
        kwargs = {}
        if workflow_name:
            kwargs.update({"workflow_name": workflow_name})

        return self.schedulerResourceApi.get_all_schedules(**kwargs)

    def get_next_few_schedule_execution_times(self,
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
        return self.schedulerResourceApi.get_next_few_schedules(cron_expression, **kwargs)

    def delete_schedule(self, name: str):
        self.schedulerResourceApi.delete_schedule(name)

    def pause_schedule(self, name: str, reason: Optional[str] = None):
        if self._legacy_scheduler_verbs:
            self._pause_resume_via_get(name, "pause", reason)
            return
        try:
            if reason is None:
                self.schedulerResourceApi.pause_schedule(name)
            else:
                self.schedulerResourceApi.pause_schedule(name, reason=reason)
        except ApiException as e:
            if e.status != 405:
                raise
            self._legacy_scheduler_verbs = True
            self._pause_resume_via_get(name, "pause", reason)

    def pause_all_schedules(self):
        self.schedulerResourceApi.pause_all_schedules()

    def resume_schedule(self, name: str):
        if self._legacy_scheduler_verbs:
            self._pause_resume_via_get(name, "resume")
            return
        try:
            self.schedulerResourceApi.resume_schedule(name)
        except ApiException as e:
            if e.status != 405:
                raise
            self._legacy_scheduler_verbs = True
            self._pause_resume_via_get(name, "resume")

    def _pause_resume_via_get(self, name: str, action: str, reason: Optional[str] = None):
        """Legacy-dialect fallback: Orkes Conductor servers map per-schedule pause/resume
        as GET (their endpoint takes no reason param; sending it is harmless). Mirrors the
        generated call in scheduler_resource_api.py with only the verb changed."""
        query_params = []
        if reason is not None:
            query_params.append(("reason", reason))
        self.api_client.call_api(
            "/scheduler/schedules/{name}/" + action, "GET",
            {"name": name},
            query_params,
            {"Accept": self.api_client.select_header_accept(["application/json"])},
            body=None,
            post_params=[],
            files={},
            response_type="object",
            auth_settings=[],
            _return_http_data_only=True,
            _preload_content=True,
            collection_formats={},
        )

    def resume_all_schedules(self):
        self.schedulerResourceApi.resume_all_schedules()

    def search_schedule_executions(self,
                                   start: Optional[int] = None,
                                   size: Optional[int] = None,
                                   sort: Optional[str] = None,
                                   free_text: Optional[str] = None,
                                   query: Optional[str] = None,
                                   ) -> SearchResultWorkflowScheduleExecutionModel:
        kwargs = {}
        if start:
            kwargs.update({"start": start})
        if size:
            kwargs.update({"size": size})
        if sort:
            kwargs.update({"sort": sort})
        if free_text:
            kwargs.update({"freeText": free_text})
        if query:
            kwargs.update({"query": query})
        return self.schedulerResourceApi.search_v21(**kwargs)

    def requeue_all_execution_records(self):
        self.schedulerResourceApi.requeue_all_execution_records()

    def set_scheduler_tags(self, tags: List[MetadataTag], name: str):
        self.schedulerResourceApi.put_tag_for_schedule(tags, name)

    def get_scheduler_tags(self, name: str) -> List[MetadataTag]:
        return self.schedulerResourceApi.get_tags_for_schedule(name)

    def delete_scheduler_tags(self, tags: List[MetadataTag], name: str) -> List[MetadataTag]:
        self.schedulerResourceApi.delete_tag_for_schedule(tags, name)
