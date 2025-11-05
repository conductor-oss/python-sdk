from typing import List

from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.workflow_bulk_resource_api import WorkflowBulkResourceApi
from conductor.client.http.models.bulk_response import BulkResponse


class WorkflowBulkResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = WorkflowBulkResourceApi(api_client)

    def delete(self, body: List[str], **kwargs) -> BulkResponse:
        """Permanently remove workflows from the system"""
        return self._api.delete(body, **kwargs)

    def pause_workflow1(self, body: List[str], **kwargs) -> BulkResponse:
        """Pause a workflow"""
        return self._api.pause_workflow1(body, **kwargs)

    def restart1(self, body: List[str], **kwargs) -> BulkResponse:
        """Restart a workflow"""
        return self._api.restart1(body, **kwargs)

    def resume_workflow1(self, body: List[str], **kwargs) -> BulkResponse:
        """Resume a workflow"""
        return self._api.resume_workflow1(body, **kwargs)

    def retry1(self, body: List[str], **kwargs) -> BulkResponse:
        """Retry a workflow"""
        return self._api.retry1(body, **kwargs)

    def terminate(self, body: List[str], **kwargs) -> BulkResponse:
        """Terminate a workflow"""
        return self._api.terminate(body, **kwargs)
