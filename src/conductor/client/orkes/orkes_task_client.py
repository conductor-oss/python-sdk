from __future__ import annotations

from typing import Dict, List, Optional

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.poll_data import PollData
from conductor.client.http.models.search_result_task import SearchResultTask
from conductor.client.http.models.search_result_task_summary import SearchResultTaskSummary
from conductor.client.http.models.signal_response import SignalResponse
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_exec_log import TaskExecLog
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.workflow import Workflow
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.task_client import TaskClient


class OrkesTaskClient(OrkesBaseClient, TaskClient):
    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def poll_task(
        self,
        task_type: str,
        worker_id: Optional[str] = None,
        domain: Optional[str] = None,
        **kwargs,
    ) -> Task:
        if worker_id:
            kwargs.update({"workerid": worker_id})
        if domain:
            kwargs.update({"domain": domain})

        return self._task_api.poll(tasktype=task_type, **kwargs)

    def batch_poll_tasks(
        self,
        task_type: str,
        worker_id: Optional[str] = None,
        count: Optional[int] = None,
        timeout_in_millisecond: Optional[int] = None,
        domain: Optional[str] = None,
        **kwargs,
    ) -> List[Task]:
        if worker_id:
            kwargs.update({"workerid": worker_id})
        if count:
            kwargs.update({"count": count})
        if timeout_in_millisecond:
            kwargs.update({"timeout": timeout_in_millisecond})
        if domain:
            kwargs.update({"domain": domain})
        return self._task_api.batch_poll(tasktype=task_type, **kwargs)

    def get_task(self, task_id: str, **kwargs) -> Task:
        return self._task_api.get_task(task_id=task_id, **kwargs)

    def update_task(self, task_result: TaskResult, **kwargs) -> str:
        return self._task_api.update_task(body=task_result, **kwargs)

    def update_task_by_ref_name(
        self,
        workflow_id: str,
        task_ref_name: str,
        status: str,
        output: object,
        worker_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        body = {"result": output}
        if worker_id:
            kwargs.update({"workerid": worker_id})
        return self._task_api.update_task1(
            body=body, workflow_id=workflow_id, task_ref_name=task_ref_name, status=status, **kwargs
        )

    def update_task_sync(
        self,
        workflow_id: str,
        task_ref_name: str,
        status: str,
        output: object,
        worker_id: Optional[str] = None,
        **kwargs,
    ) -> Workflow:
        if not isinstance(output, dict):
            output = {"result": output}
        body = output
        if worker_id:
            kwargs.update({"workerid": worker_id})
        return self._task_api.update_task_sync(
            body=body, workflow_id=workflow_id, task_ref_name=task_ref_name, status=status, **kwargs
        )

    def get_queue_size_for_task(self, task_type: str, **kwargs) -> int:
        queueSizesByTaskType = self._task_api.size(task_type=[task_type], **kwargs)
        queueSize = queueSizesByTaskType.get(task_type, 0)
        return queueSize

    def add_task_log(self, task_id: str, log_message: str, **kwargs) -> None:
        self._task_api.log(body=log_message, task_id=task_id, **kwargs)

    def get_task_logs(self, task_id: str, **kwargs) -> List[TaskExecLog]:
        return self._task_api.get_task_logs(task_id=task_id, **kwargs)

    def get_task_poll_data(self, task_type: str, **kwargs) -> List[PollData]:
        return self._task_api.get_poll_data(task_type=task_type, **kwargs)

    def get_all_poll_data(self, **kwargs) -> Dict[str, object]:
        return self._task_api.get_all_poll_data(**kwargs)

    def requeue_pending_task(self, task_type: str, **kwargs) -> str:
        return self._task_api.requeue_pending_task(task_type=task_type, **kwargs)

    def search_tasks(
        self,
        start: int = 0,
        size: int = 100,
        sort: Optional[str] = None,
        free_text: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs,
    ) -> SearchResultTaskSummary:
        """Search for tasks based on payload and other parameters

        Args:
            start: Start index for pagination
            size: Page size
            sort: Sort options as sort=<field>:ASC|DESC e.g. sort=name&sort=workflowId:DESC
            free_text: Free text search
            query: Query string
        """
        return self._task_api.search1(
            start=start, size=size, sort=sort, free_text=free_text, query=query, **kwargs
        )

    def search_tasks_v2(
        self,
        start: int = 0,
        size: int = 100,
        sort: Optional[str] = None,
        free_text: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs,
    ) -> SearchResultTask:
        """Search for tasks based on payload and other parameters

        Args:
            start: Start index for pagination
            size: Page size
            sort: Sort options as sort=<field>:ASC|DESC e.g. sort=name&sort=workflowId:DESC
            free_text: Free text search
            query: Query string
        """
        return self._task_api.search_v21(
            start=start, size=size, sort=sort, free_text=free_text, query=query, **kwargs
        )

    def signal_workflow_task_async(
        self, workflow_id: str, status: str, body: Dict[str, object], **kwargs
    ) -> None:
        self._task_api.signal_workflow_task_async(
            workflow_id=workflow_id, status=status, body=body, **kwargs
        )

    def signal_workflow_task_sync(
        self, workflow_id: str, status: str, body: Dict[str, object], **kwargs
    ) -> SignalResponse:
        return self._task_api.signal_workflow_task_sync(
            workflow_id=workflow_id, status=status, body=body, **kwargs
        )

    def get_task_queue_sizes(self, **kwargs) -> Dict[str, int]:
        """Get the size of all task queues"""
        return self._task_api.all(**kwargs)

    def get_task_queue_sizes_verbose(self, **kwargs) -> Dict[str, Dict[str, Dict[str, int]]]:
        """Get detailed information about all task queues"""
        return self._task_api.all_verbose(**kwargs)
