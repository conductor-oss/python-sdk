from typing import Dict, List

from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.task_resource_api import TaskResourceApi
from conductor.client.http.models.poll_data import PollData
from conductor.client.http.models.search_result_task import SearchResultTask
from conductor.client.http.models.search_result_task_summary import SearchResultTaskSummary
from conductor.client.http.models.signal_response import SignalResponse
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_exec_log import TaskExecLog
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.workflow import Workflow


class TaskResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = TaskResourceApi(api_client)

    def all(self, **kwargs) -> Dict[str, int]:
        """Get the details about each queue"""
        return self._api.all(**kwargs)

    def all_verbose(self, **kwargs) -> Dict[str, Dict[str, Dict[str, int]]]:
        """Get the details about each queue with verbose information"""
        return self._api.all_verbose(**kwargs)

    def batch_poll(self, tasktype: str, **kwargs) -> List[Task]:
        """Batch poll for a task of a certain type"""
        return self._api.batch_poll(tasktype, **kwargs)

    def get_all_poll_data(self, **kwargs) -> Dict[str, object]:
        """Get the details about all poll data"""
        return self._api.get_all_poll_data(**kwargs)

    def get_poll_data(self, task_type: str, **kwargs) -> List[PollData]:
        """Get the details about poll data for a task type"""
        return self._api.get_poll_data(task_type, **kwargs)

    def get_task(self, task_id: str, **kwargs) -> Task:
        """Get a task by its ID"""
        return self._api.get_task(task_id, **kwargs)

    def get_task_logs(self, task_id: str, **kwargs) -> List[TaskExecLog]:
        """Get the logs for a task"""
        return self._api.get_task_logs(task_id, **kwargs)

    def log(self, body: str, task_id: str, **kwargs) -> None:
        """Log a message for a task"""
        return self._api.log(body, task_id, **kwargs)

    def poll(self, tasktype: str, **kwargs) -> Task:
        """Poll for a task of a certain type"""
        return self._api.poll(tasktype, **kwargs)

    def requeue_pending_task(self, task_type: str, **kwargs) -> str:
        """Requeue a pending task"""
        return self._api.requeue_pending_task(task_type, **kwargs)

    def search1(self, **kwargs) -> SearchResultTaskSummary:
        """Search for tasks"""
        return self._api.search1(**kwargs)

    def search_v21(self, **kwargs) -> SearchResultTask:
        """Search for tasks"""
        return self._api.search_v21(**kwargs)

    def size(self, **kwargs) -> Dict[str, int]:
        """Get the size of a task type"""
        return self._api.size(**kwargs)

    def update_task(self, body: TaskResult, **kwargs) -> str:
        """Update a task"""
        return self._api.update_task(body, **kwargs)

    def update_task1(
        self, body: Dict[str, object], workflow_id: str, task_ref_name: str, status: str, **kwargs
    ) -> str:
        """Update a task"""
        return self._api.update_task1(body, workflow_id, task_ref_name, status, **kwargs)

    def update_task_sync(
        self, body: Dict[str, object], workflow_id: str, task_ref_name: str, status: str, **kwargs
    ) -> Workflow:
        """Update a task synchronously"""
        return self._api.update_task_sync(body, workflow_id, task_ref_name, status, **kwargs)

    def signal_workflow_task_async(
        self, workflow_id: str, status: str, body: Dict[str, object], **kwargs
    ) -> None:
        """Signal a workflow task asynchronously"""
        return self._api.signal_workflow_task_async(workflow_id, status, body, **kwargs)

    def signal_workflow_task_sync(
        self, workflow_id: str, status: str, body: Dict[str, object], **kwargs
    ) -> SignalResponse:
        """Signal a workflow task synchronously"""
        return self._api.signal_workflow_task_sync(workflow_id, status, body, **kwargs)
