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
        """Initialize the OrkesTaskClient with configuration.

        Args:
            configuration: Configuration object containing server settings and authentication

        Example:
            ```python
            from conductor.client.configuration.configuration import Configuration

            config = Configuration(server_api_url="http://localhost:8080/api")
            task_client = OrkesTaskClient(config)
            ```
        """
        super().__init__(configuration)

    def poll_task(
        self,
        task_type: str,
        worker_id: Optional[str] = None,
        domain: Optional[str] = None,
        **kwargs,
    ) -> Task:
        """Poll for a single task of a certain type.

        Args:
            task_type: Type of task to poll for
            worker_id: Optional worker ID for tracking
            domain: Optional domain for task isolation
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Task instance if a task is available

        Example:
            ```python
            task = task_client.poll_task("process_order", worker_id="worker-1")
            if task:
                print(f"Got task: {task.task_id}")
                # Process the task
            ```
        """
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
        """Poll for multiple tasks of a certain type.

        Args:
            task_type: Type of task to poll for
            worker_id: Optional worker ID for tracking
            count: Maximum number of tasks to poll
            timeout_in_millisecond: Timeout for the poll operation in milliseconds
            domain: Optional domain for task isolation
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of Task instances

        Example:
            ```python
            tasks = task_client.batch_poll_tasks(
                "process_order",
                worker_id="worker-1",
                count=10,
                timeout_in_millisecond=5000
            )
            print(f"Got {len(tasks)} tasks")
            ```
        """
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
        """Get a task by ID.

        Args:
            task_id: Unique identifier for the task
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Task instance

        Example:
            ```python
            task = task_client.get_task("task-123")
            print(f"Task status: {task.status}")
            ```
        """
        return self._task_api.get_task(task_id=task_id, **kwargs)

    def update_task(self, task_result: TaskResult, **kwargs) -> str:
        """Update a task with result.

        Args:
            task_result: Task result containing status and output
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Workflow ID as string

        Example:
            ```python
            from conductor.client.http.models.task_result import TaskResult

            result = TaskResult(
                task_id="task-123",
                status="COMPLETED",
                output_data={"result": "success"}
            )
            workflow_id = task_client.update_task(result)
            print(f"Updated task in workflow: {workflow_id}")
            ```
        """
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
        """Update a task by reference name within a workflow.

        Args:
            workflow_id: ID of the workflow containing the task
            task_ref_name: Reference name of the task in the workflow
            status: New status for the task (e.g., "COMPLETED", "FAILED")
            output: Output data for the task
            worker_id: Optional worker ID for tracking
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Workflow ID as string

        Example:
            ```python
            workflow_id = task_client.update_task_by_ref_name(
                workflow_id="workflow-123",
                task_ref_name="process_order",
                status="COMPLETED",
                output={"order_id": "12345", "status": "processed"}
            )
            ```
        """
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
        """Update a task synchronously and get the updated workflow.

        Args:
            workflow_id: ID of the workflow containing the task
            task_ref_name: Reference name of the task in the workflow
            status: New status for the task
            output: Output data for the task (dict or other object)
            worker_id: Optional worker ID for tracking
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Workflow instance with updated state

        Example:
            ```python
            workflow = task_client.update_task_sync(
                workflow_id="workflow-123",
                task_ref_name="process_order",
                status="COMPLETED",
                output={"order_id": "12345"}
            )
            print(f"Workflow status: {workflow.status}")
            ```
        """
        if not isinstance(output, dict):
            output = {"result": output}
        body = output
        if worker_id:
            kwargs.update({"workerid": worker_id})
        return self._task_api.update_task_sync(
            body=body, workflow_id=workflow_id, task_ref_name=task_ref_name, status=status, **kwargs
        )

    def get_queue_size_for_task(self, task_type: str, **kwargs) -> int:
        """Get the queue size for a specific task type.

        Args:
            task_type: Type of task to check
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Queue size as integer

        Example:
            ```python
            size = task_client.get_queue_size_for_task("process_order")
            print(f"Queue size: {size}")
            ```
        """
        queueSizesByTaskType = self._task_api.size(task_type=[task_type], **kwargs)
        queueSize = queueSizesByTaskType.get(task_type, 0)
        return queueSize

    def add_task_log(self, task_id: str, log_message: str, **kwargs) -> None:
        """Add a log message to a task.

        Args:
            task_id: Unique identifier for the task
            log_message: Log message to add
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            task_client.add_task_log("task-123", "Processing started")
            ```
        """
        self._task_api.log(body=log_message, task_id=task_id, **kwargs)

    def get_task_logs(self, task_id: str, **kwargs) -> List[TaskExecLog]:
        """Get all log messages for a task.

        Args:
            task_id: Unique identifier for the task
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TaskExecLog instances

        Example:
            ```python
            logs = task_client.get_task_logs("task-123")
            for log in logs:
                print(f"{log.created_time}: {log.log}")
            ```
        """
        return self._task_api.get_task_logs(task_id=task_id, **kwargs)

    def get_task_poll_data(self, task_type: str, **kwargs) -> List[PollData]:
        """Get poll data for a specific task type.

        Args:
            task_type: Type of task to get poll data for
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of PollData instances

        Example:
            ```python
            poll_data = task_client.get_task_poll_data("process_order")
            for data in poll_data:
                print(f"Worker: {data.worker_id}, Last poll: {data.last_poll_time}")
            ```
        """
        return self._task_api.get_poll_data(task_type=task_type, **kwargs)

    def get_all_poll_data(self, **kwargs) -> Dict[str, object]:
        """Get poll data for all task types.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping task types to poll data

        Example:
            ```python
            all_poll_data = task_client.get_all_poll_data()
            for task_type, data in all_poll_data.items():
                print(f"Task type: {task_type}")
            ```
        """
        return self._task_api.get_all_poll_data(**kwargs)

    def requeue_pending_task(self, task_type: str, **kwargs) -> str:
        """Requeue all pending tasks of a certain type.

        Args:
            task_type: Type of task to requeue
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Result message as string

        Example:
            ```python
            result = task_client.requeue_pending_task("process_order")
            print(f"Requeue result: {result}")
            ```
        """
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
        """Search for tasks based on payload and other parameters.

        Args:
            start: Start index for pagination
            size: Page size
            sort: Sort options as sort=<field>:ASC|DESC e.g. sort=name&sort=workflowId:DESC
            free_text: Free text search
            query: Query string
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            SearchResultTaskSummary with matching tasks

        Example:
            ```python
            results = task_client.search_tasks(
                start=0,
                size=20,
                sort="startTime:DESC",
                query="taskType='process_order'"
            )
            print(f"Found {results.total_hits} tasks")
            ```
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
        """Search for tasks based on payload and other parameters (v2 API).

        Args:
            start: Start index for pagination
            size: Page size
            sort: Sort options as sort=<field>:ASC|DESC e.g. sort=name&sort=workflowId:DESC
            free_text: Free text search
            query: Query string
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            SearchResultTask with matching tasks

        Example:
            ```python
            results = task_client.search_tasks_v2(
                start=0,
                size=20,
                sort="startTime:DESC",
                free_text="order"
            )
            print(f"Found {results.total_hits} tasks")
            for task in results.results:
                print(f"Task: {task.task_id}, Status: {task.status}")
            ```
        """
        return self._task_api.search_v21(
            start=start, size=size, sort=sort, free_text=free_text, query=query, **kwargs
        )

    def signal_workflow_task_async(
        self, workflow_id: str, status: str, body: Dict[str, object], **kwargs
    ) -> None:
        """Signal a workflow task asynchronously.

        Args:
            workflow_id: ID of the workflow containing the task
            status: Status to signal
            body: Signal payload
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            task_client.signal_workflow_task_async(
                workflow_id="workflow-123",
                status="COMPLETED",
                body={"result": "success"}
            )
            ```
        """
        self._task_api.signal_workflow_task_async(
            workflow_id=workflow_id, status=status, body=body, **kwargs
        )

    def signal_workflow_task_sync(
        self, workflow_id: str, status: str, body: Dict[str, object], **kwargs
    ) -> SignalResponse:
        """Signal a workflow task synchronously.

        Args:
            workflow_id: ID of the workflow containing the task
            status: Status to signal
            body: Signal payload
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            SignalResponse with signal result

        Example:
            ```python
            response = task_client.signal_workflow_task_sync(
                workflow_id="workflow-123",
                status="COMPLETED",
                body={"result": "success"}
            )
            print(f"Signal response: {response.status}")
            ```
        """
        return self._task_api.signal_workflow_task_sync(
            workflow_id=workflow_id, status=status, body=body, **kwargs
        )

    def get_task_queue_sizes(self, **kwargs) -> Dict[str, int]:
        """Get the size of all task queues.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping task types to queue sizes

        Example:
            ```python
            queue_sizes = task_client.get_task_queue_sizes()
            for task_type, size in queue_sizes.items():
                print(f"Task: {task_type}, Queue Size: {size}")
            ```
        """
        return self._task_api.all(**kwargs)

    def get_task_queue_sizes_verbose(self, **kwargs) -> Dict[str, Dict[str, Dict[str, int]]]:
        """Get detailed information about all task queues.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Nested dictionary with detailed queue information

        Example:
            ```python
            queue_info = task_client.get_task_queue_sizes_verbose()
            for task_type, details in queue_info.items():
                print(f"Task type: {task_type}")
                for domain, stats in details.items():
                    print(f"  Domain: {domain}, Stats: {stats}")
            ```
        """
        return self._task_api.all_verbose(**kwargs)
