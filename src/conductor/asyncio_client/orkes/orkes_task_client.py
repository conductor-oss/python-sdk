from __future__ import annotations

from typing import Any, Dict, List, Optional

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.models.poll_data_adapter import PollDataAdapter
from conductor.asyncio_client.adapters.models.search_result_task_summary_adapter import (
    SearchResultTaskSummaryAdapter,
)
from conductor.asyncio_client.adapters.models.task_adapter import TaskAdapter
from conductor.asyncio_client.adapters.models.task_exec_log_adapter import TaskExecLogAdapter
from conductor.asyncio_client.adapters.models.task_result_adapter import TaskResultAdapter
from conductor.asyncio_client.adapters.models.workflow_adapter import WorkflowAdapter
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient


class OrkesTaskClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        super().__init__(configuration, api_client)

    # Task Polling Operations
    async def poll_for_task(
        self, task_type: str, worker_id: Optional[str] = None, domain: Optional[str] = None
    ) -> Optional[TaskAdapter]:
        """Poll for a single task of a certain type"""
        return await self.task_api.poll(tasktype=task_type, workerid=worker_id, domain=domain)

    async def poll_for_task_batch(
        self,
        task_type: str,
        worker_id: Optional[str] = None,
        count: int = 1,
        timeout: int = 100,
        domain: Optional[str] = None,
    ) -> List[TaskAdapter]:
        """Poll for multiple tasks in batch"""
        return await self.task_api.batch_poll(
            tasktype=task_type,
            workerid=worker_id,
            count=count,
            timeout=timeout,
            domain=domain,
        )

    # Task Operations
    async def get_task(self, task_id: str) -> TaskAdapter:
        """Get task by ID"""
        return await self.task_api.get_task(task_id=task_id)

    async def update_task(self, task_result: TaskResultAdapter) -> str:
        """Update task with result"""
        return await self.task_api.update_task(task_result=task_result)

    async def update_task_by_ref_name(
        self,
        workflow_id: str,
        task_ref_name: str,
        status: str,
        output: Dict[str, Dict[str, Any]],
        worker_id: Optional[str] = None,
    ) -> str:
        """Update task by workflow ID and task reference name"""
        body = {"result": output}

        return await self.task_api.update_task1(
            workflow_id=workflow_id,
            task_ref_name=task_ref_name,
            status=status,
            request_body=body,
            workerid=worker_id,
        )

    async def update_task_sync(
        self,
        workflow_id: str,
        task_ref_name: str,
        status: str,
        output: Dict[str, Any],
        worker_id: Optional[str] = None,
    ) -> WorkflowAdapter:
        """Update task synchronously by workflow ID and task reference name"""
        body = {"result": output}
        return await self.task_api.update_task_sync(
            workflow_id=workflow_id,
            task_ref_name=task_ref_name,
            status=status,
            request_body=body,
            workerid=worker_id,
        )

    # Task Queue Operations
    async def get_task_queue_sizes(self) -> Dict[str, int]:
        """Get the size of all task queues"""
        return await self.task_api.all()

    async def get_task_queue_sizes_verbose(
        self,
    ) -> Dict[str, Dict[str, Dict[str, int]]]:
        """Get detailed information about all task queues"""
        return await self.task_api.all_verbose()

    # Poll Data Operations
    async def get_all_poll_data(
        self,
        worker_size: Optional[int] = None,
        worker_opt: Optional[str] = None,
        queue_size: Optional[int] = None,
        queue_opt: Optional[str] = None,
        last_poll_time_size: Optional[int] = None,
        last_poll_time_opt: Optional[str] = None,
    ) -> Dict[str, object]:
        """Get the last poll data for all task types"""
        return await self.task_api.get_all_poll_data(
            worker_size=worker_size,
            worker_opt=worker_opt,
            queue_size=queue_size,
            queue_opt=queue_opt,
            last_poll_time_size=last_poll_time_size,
            last_poll_time_opt=last_poll_time_opt,
        )

    async def get_poll_data(self, task_type: str) -> List[PollDataAdapter]:
        """Get the last poll data for a specific task type"""
        return await self.task_api.get_poll_data(task_type=task_type)

    # Task Logging Operations
    async def get_task_logs(self, task_id: str) -> List[TaskExecLogAdapter]:
        """Get task execution logs"""
        return await self.task_api.get_task_logs(task_id=task_id)

    async def log_task(self, task_id: str, log_message: str) -> None:
        """Log task execution details"""
        await self.task_api.log(task_id=task_id, body=log_message)

    # Task Search Operations
    async def search_tasks(
        self,
        start: int = 0,
        size: int = 100,
        sort: Optional[str] = None,
        free_text: Optional[str] = None,
        query: Optional[str] = None,
    ) -> SearchResultTaskSummaryAdapter:
        """Search for tasks based on payload and other parameters

        Args:
            start: Start index for pagination
            size: Page size
            sort: Sort options as sort=<field>:ASC|DESC e.g. sort=name&sort=workflowId:DESC
            free_text: Free text search
            query: Query string
        """
        return await self.task_api.search1(
            start=start, size=size, sort=sort, free_text=free_text, query=query
        )

    # Task Queue Management
    async def requeue_pending_tasks(self, task_type: str) -> str:
        """Requeue all pending tasks of a given task type"""
        return await self.task_api.requeue_pending_task(task_type=task_type)

    # Utility Methods
    async def get_queue_size_for_task_type(self, task_type: List[str]) -> Dict[str, int]:
        """Get queue size for a specific task type"""
        return await self.task_api.size(task_type=task_type)
