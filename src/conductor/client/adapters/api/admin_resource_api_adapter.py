from typing import Dict, List

from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.admin_resource_api import AdminResourceApi
from conductor.client.http.models.task import Task


class AdminResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = AdminResourceApi(api_client)

    def clear_task_execution_cache(self, task_def_name: str, **kwargs) -> None:
        """Remove execution cached values for the task"""
        return self._api.clear_task_execution_cache(task_def_name, **kwargs)

    def get_redis_usage(self, **kwargs) -> Dict[str, object]:
        """Get the Redis usage"""
        return self._api.get_redis_usage(**kwargs)

    def requeue_sweep(self, workflow_id: str, **kwargs) -> str:
        """Queue up all the running workflows for sweep"""
        return self._api.requeue_sweep(workflow_id, **kwargs)

    def verify_and_repair_workflow_consistency(self, workflow_id: str, **kwargs) -> str:
        """Verify and repair workflow consistency"""
        return self._api.verify_and_repair_workflow_consistency(workflow_id, **kwargs)

    def view(self, tasktype: str, **kwargs) -> List[Task]:
        """View the task type"""
        return self._api.view(tasktype, **kwargs)
