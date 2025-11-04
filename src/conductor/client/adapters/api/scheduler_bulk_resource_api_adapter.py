from typing import List

from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.scheduler_bulk_resource_api import SchedulerBulkResourceApi
from conductor.client.http.models.bulk_response import BulkResponse


class SchedulerBulkResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = SchedulerBulkResourceApi(api_client)

    def pause_schedules(self, body: List[str], **kwargs) -> BulkResponse:
        """Pause the list of schedules"""
        return self._api.pause_schedules(body, **kwargs)

    def resume_schedules(self, body: List[str], **kwargs) -> BulkResponse:
        """Resume the list of schedules"""
        return self._api.resume_schedules(body, **kwargs)
