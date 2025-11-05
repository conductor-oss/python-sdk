from __future__ import annotations

from typing import Any, Dict, List, Optional, cast

from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

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
        """Initialize the OrkesTaskClient with configuration and API client.

        Args:
            configuration: Configuration object containing server settings and authentication
            api_client: ApiClient instance for making API requests

        Example:
            ```python
            from conductor.asyncio_client.configuration.configuration import Configuration
            from conductor.asyncio_client.adapters import ApiClient

            config = Configuration(server_api_url="http://localhost:8080/api")
            api_client = ApiClient(configuration=config)
            task_client = OrkesTaskClient(config, api_client)
            ```
        """
        super().__init__(configuration, api_client)

    # Task Polling Operations
    @deprecated("poll_for_task is deprecated; use poll_task instead")
    @typing_deprecated("poll_for_task is deprecated; use poll_task instead")
    async def poll_for_task(
        self, task_type: str, worker_id: Optional[str] = None, domain: Optional[str] = None
    ) -> Optional[TaskAdapter]:
        """Poll for a single task of a certain type.

        .. deprecated::
            Use poll_task instead for consistent API interface.

        Args:
            task_type: Type of task to poll for
            worker_id: Optional worker ID for tracking
            domain: Optional domain for task isolation

        Returns:
            TaskAdapter instance if a task is available, None otherwise

        Example:
            ```python
            task = await task_client.poll_for_task("process_order", worker_id="worker-1")
            ```
        """
        return await self._task_api.poll(tasktype=task_type, workerid=worker_id, domain=domain)

    async def poll_task(
        self,
        task_type: str,
        worker_id: Optional[str] = None,
        domain: Optional[str] = None,
        **kwargs,
    ) -> Optional[TaskAdapter]:
        """Poll for a single task of a certain type.

        Args:
            task_type: Type of task to poll for
            worker_id: Optional worker ID for tracking
            domain: Optional domain for task isolation
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            TaskAdapter instance if a task is available, None otherwise

        Example:
            ```python
            task = await task_client.poll_task("process_order", worker_id="worker-1")
            if task:
                print(f"Got task: {task.task_id}")
                # Process the task
            ```
        """
        return await self._task_api.poll(
            tasktype=task_type, workerid=worker_id, domain=domain, **kwargs
        )

    @deprecated("poll_for_task_batch is deprecated; use batch_poll_tasks instead")
    @typing_deprecated("poll_for_task_batch is deprecated; use batch_poll_tasks instead")
    async def poll_for_task_batch(
        self,
        task_type: str,
        worker_id: Optional[str] = None,
        count: int = 1,
        timeout: int = 100,
        domain: Optional[str] = None,
    ) -> List[TaskAdapter]:
        """Poll for multiple tasks in batch.

        .. deprecated::
            Use batch_poll_tasks instead for consistent API interface.

        Args:
            task_type: Type of task to poll for
            worker_id: Optional worker ID for tracking
            count: Number of tasks to poll for (default: 1)
            timeout: Timeout in milliseconds (default: 100)
            domain: Optional domain for task isolation

        Returns:
            List of TaskAdapter instances

        Example:
            ```python
            tasks = await task_client.poll_for_task_batch("process_order", count=5)
            ```
        """
        return await self._task_api.batch_poll(
            tasktype=task_type,
            workerid=worker_id,
            count=count,
            timeout=timeout,
            domain=domain,
        )

    async def batch_poll_tasks(
        self,
        task_type: str,
        worker_id: Optional[str] = None,
        count: int = 1,
        timeout: int = 100,
        domain: Optional[str] = None,
        **kwargs,
    ) -> List[TaskAdapter]:
        """Poll for multiple tasks in batch.

        Efficiently retrieves multiple tasks in a single operation.

        Args:
            task_type: Type of task to poll for
            worker_id: Optional worker ID for tracking
            count: Number of tasks to poll for (default: 1)
            timeout: Timeout in milliseconds (default: 100)
            domain: Optional domain for task isolation
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TaskAdapter instances

        Example:
            ```python
            # Poll for up to 10 tasks
            tasks = await task_client.batch_poll_tasks(
                "process_order",
                worker_id="worker-1",
                count=10,
                timeout=5000
            )
            print(f"Received {len(tasks)} tasks to process")
            ```
        """
        return await self._task_api.batch_poll(
            tasktype=task_type,
            workerid=worker_id,
            count=count,
            timeout=timeout,
            domain=domain,
            **kwargs,
        )

    # Task Operations
    async def get_task(self, task_id: str, **kwargs) -> TaskAdapter:
        """Get task by ID.

        Args:
            task_id: Unique identifier for the task
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            TaskAdapter instance containing task details

        Example:
            ```python
            task = await task_client.get_task("task-123")
            print(f"Status: {task.status}, Output: {task.output_data}")
            ```
        """
        return await self._task_api.get_task(task_id=task_id, **kwargs)

    async def update_task(self, task_result: TaskResultAdapter, **kwargs) -> str:
        """Update task with result.

        Args:
            task_result: Task result containing status, output data, and logs
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Task ID as string

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.task_result_adapter import TaskResultAdapter

            result = TaskResultAdapter(
                task_id="task-123",
                status="COMPLETED",
                output_data={"result": "success", "data": {...}}
            )
            await task_client.update_task(result)
            ```
        """
        return await self._task_api.update_task(task_result=task_result, **kwargs)

    async def update_task_by_ref_name(
        self,
        workflow_id: str,
        task_ref_name: str,
        status: str,
        output: Dict[str, Dict[str, Any]],
        worker_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Update task by workflow ID and task reference name.

        Useful when you don't have the task ID but know the workflow and task reference.

        Args:
            workflow_id: ID of the workflow containing the task
            task_ref_name: Reference name of the task in the workflow
            status: New task status (e.g., "COMPLETED", "FAILED")
            output: Task output data
            worker_id: Optional worker ID
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Task ID as string

        Example:
            ```python
            await task_client.update_task_by_ref_name(
                workflow_id="workflow-123",
                task_ref_name="process_order_ref",
                status="COMPLETED",
                output={"order_id": "12345", "status": "processed"}
            )
            ```
        """
        body = {"result": output}

        return await self._task_api.update_task1(
            workflow_id=workflow_id,
            task_ref_name=task_ref_name,
            status=status,
            request_body=body,
            workerid=worker_id,
            **kwargs,
        )

    async def update_task_sync(
        self,
        workflow_id: str,
        task_ref_name: str,
        status: str,
        output: Dict[str, Any],
        worker_id: Optional[str] = None,
        **kwargs,
    ) -> WorkflowAdapter:
        """Update task synchronously by workflow ID and task reference name.

        Updates a task and waits for the workflow to process the update before returning.

        Args:
            workflow_id: ID of the workflow containing the task
            task_ref_name: Reference name of the task in the workflow
            status: New task status (e.g., "COMPLETED", "FAILED")
            output: Task output data
            worker_id: Optional worker ID
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowAdapter instance with updated workflow state

        Example:
            ```python
            workflow = await task_client.update_task_sync(
                workflow_id="workflow-123",
                task_ref_name="validate_order_ref",
                status="COMPLETED",
                output={"is_valid": True}
            )
            print(f"Workflow status: {workflow.status}")
            ```
        """
        body = {"result": output}
        return await self._task_api.update_task_sync(
            workflow_id=workflow_id,
            task_ref_name=task_ref_name,
            status=status,
            request_body=body,
            workerid=worker_id,
            **kwargs,
        )

    # Task Queue Operations
    async def get_task_queue_sizes(self, **kwargs) -> Dict[str, int]:
        """Get the size of all task queues.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping task types to queue sizes

        Example:
            ```python
            queue_sizes = await task_client.get_task_queue_sizes()
            for task_type, size in queue_sizes.items():
                print(f"{task_type}: {size} tasks pending")
            ```
        """
        return await self._task_api.all(**kwargs)

    async def get_task_queue_sizes_verbose(self, **kwargs) -> Dict[str, Dict[str, Dict[str, int]]]:
        """Get detailed information about all task queues.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Nested dictionary with detailed queue information

        Example:
            ```python
            verbose_info = await task_client.get_task_queue_sizes_verbose()
            ```
        """
        return await self._task_api.all_verbose(**kwargs)

    # Poll Data Operations
    async def get_all_poll_data(
        self,
        worker_size: Optional[int] = None,
        worker_opt: Optional[str] = None,
        queue_size: Optional[int] = None,
        queue_opt: Optional[str] = None,
        last_poll_time_size: Optional[int] = None,
        last_poll_time_opt: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, object]:
        """Get the last poll data for all task types.

        Args:
            worker_size: Worker size parameter
            worker_opt: Worker option parameter
            queue_size: Queue size parameter
            queue_opt: Queue option parameter
            last_poll_time_size: Last poll time size parameter
            last_poll_time_opt: Last poll time option parameter
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary with poll data for all task types

        Example:
            ```python
            poll_data = await task_client.get_all_poll_data()
            ```
        """
        return await self._task_api.get_all_poll_data(
            worker_size=worker_size,
            worker_opt=worker_opt,
            queue_size=queue_size,
            queue_opt=queue_opt,
            last_poll_time_size=last_poll_time_size,
            last_poll_time_opt=last_poll_time_opt,
            **kwargs,
        )

    @deprecated("get_poll_data is deprecated; use get_task_poll_data instead")
    @typing_deprecated("get_poll_data is deprecated; use get_task_poll_data instead")
    async def get_poll_data(self, task_type: str) -> List[PollDataAdapter]:
        """Get the last poll data for a specific task type.

        .. deprecated::
            Use get_task_poll_data instead for consistent API interface.

        Args:
            task_type: Type of task

        Returns:
            List of PollDataAdapter instances

        Example:
            ```python
            poll_data = await task_client.get_poll_data("process_order")
            ```
        """
        return await self._task_api.get_poll_data(task_type=task_type)

    async def get_task_poll_data(self, task_type: str, **kwargs) -> List[PollDataAdapter]:
        """Get the last poll data for a specific task type.

        Args:
            task_type: Type of task
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of PollDataAdapter instances

        Example:
            ```python
            poll_data = await task_client.get_task_poll_data("process_order")
            for data in poll_data:
                print(f"Worker: {data.worker_id}, Last poll: {data.last_poll_time}")
            ```
        """
        return await self._task_api.get_poll_data(task_type=task_type, **kwargs)

    # Task Logging Operations
    async def get_task_logs(self, task_id: str) -> List[TaskExecLogAdapter]:
        """Get task execution logs.

        Args:
            task_id: Unique identifier for the task

        Returns:
            List of TaskExecLogAdapter instances containing log entries

        Example:
            ```python
            logs = await task_client.get_task_logs("task-123")
            for log in logs:
                print(f"{log.created_time}: {log.log}")
            ```
        """
        return await self._task_api.get_task_logs(task_id=task_id)

    @deprecated("log_task is deprecated; use add_task_log instead")
    @typing_deprecated("log_task is deprecated; use add_task_log instead")
    async def log_task(self, task_id: str, log_message: str) -> None:
        """Log task execution details.

        .. deprecated::
            Use add_task_log instead for consistent API interface.

        Args:
            task_id: Unique identifier for the task
            log_message: Log message to add

        Returns:
            None

        Example:
            ```python
            await task_client.log_task("task-123", "Processing order...")
            ```
        """
        await self._task_api.log(task_id=task_id, body=log_message)

    async def add_task_log(self, task_id: str, log_message: str, **kwargs) -> None:
        """Add a task log.

        Args:
            task_id: Unique identifier for the task
            log_message: Log message to add
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await task_client.add_task_log("task-123", "Starting order processing")
            await task_client.add_task_log("task-123", "Order validated successfully")
            ```
        """
        await self._task_api.log(task_id=task_id, body=log_message, **kwargs)

    # Task Search Operations
    async def search_tasks(
        self,
        start: int = 0,
        size: int = 100,
        sort: Optional[str] = None,
        free_text: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs,
    ) -> SearchResultTaskSummaryAdapter:
        """Search for tasks based on payload and other parameters.

        Args:
            start: Start index for pagination (default: 0)
            size: Page size (default: 100)
            sort: Sort options as sort=<field>:ASC|DESC e.g. sort=name&sort=workflowId:DESC
            free_text: Free text search
            query: Structured query string
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            SearchResultTaskSummaryAdapter with matching tasks

        Example:
            ```python
            # Search for failed tasks
            results = await task_client.search_tasks(
                query="status:FAILED",
                size=50
            )
            print(f"Found {results.total_hits} failed tasks")

            # Free text search
            results = await task_client.search_tasks(free_text="order processing")
            ```
        """
        return await self._task_api.search1(
            start=start, size=size, sort=sort, free_text=free_text, query=query, **kwargs
        )

    # Task Queue Management
    async def requeue_pending_tasks(self, task_type: str, **kwargs) -> str:
        """Requeue all pending tasks of a given task type.

        Args:
            task_type: Type of task to requeue
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Result message as string

        Example:
            ```python
            result = await task_client.requeue_pending_tasks("process_order")
            print(result)
            ```
        """
        return await self._task_api.requeue_pending_task(task_type=task_type, **kwargs)

    # Utility Methods
    @deprecated("get_queue_size_for_task_type is deprecated; use get_queue_size_for_task instead")
    @typing_deprecated(
        "get_queue_size_for_task_type is deprecated; use get_queue_size_for_task instead"
    )
    async def get_queue_size_for_task_type(self, task_type: List[str]) -> Dict[str, int]:
        """Get queue size for a specific task type.

        .. deprecated::
            Use get_queue_size_for_task instead for consistent API interface.

        Args:
            task_type: List containing the task type name

        Returns:
            Dictionary mapping task types to queue sizes

        Example:
            ```python
            sizes = await task_client.get_queue_size_for_task_type(["process_order"])
            ```
        """
        return await self._task_api.size(task_type=task_type)

    async def get_queue_size_for_task(self, task_type: List[str], **kwargs) -> int:
        """Get queue size for a specific task type.

        Args:
            task_type: List containing the task type name
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Queue size as integer

        Example:
            ```python
            size = await task_client.get_queue_size_for_task(["process_order"])
            print(f"Pending tasks: {size}")
            ```
        """
        queue_sizes_by_task_type = await self._task_api.size(task_type=task_type, **kwargs)

        if isinstance(task_type, list) and task_type:
            actual_task_type = task_type[0]
        else:
            actual_task_type = task_type

        queue_sizes_dict = cast(Dict[str, int], queue_sizes_by_task_type)
        queue_size = queue_sizes_dict.get(actual_task_type, 0)

        return queue_size
