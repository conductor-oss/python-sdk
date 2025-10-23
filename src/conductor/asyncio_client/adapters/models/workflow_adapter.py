from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from conductor.asyncio_client.adapters.models.task_adapter import TaskAdapter

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import Workflow


class WorkflowAdapter(Workflow):
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None
    workflow_definition: Optional["WorkflowDefAdapter"] = Field(  # type: ignore[assignment]
        default=None, alias="workflowDefinition"
    )
    tasks: Optional[List["TaskAdapter"]] = None  # type: ignore[assignment]
    history: Optional[List["WorkflowAdapter"]] = None  # type: ignore[assignment]

    def is_completed(self) -> bool:
        """Checks if the workflow has completed
        :return: True if the workflow status is COMPLETED, FAILED, TIMED_OUT, or TERMINATED

        Example:
            workflow = WorkflowAdapter(status="COMPLETED")
            if workflow.is_completed():
                print("Workflow has finished")
        """
        return self.status in ("COMPLETED", "FAILED", "TIMED_OUT", "TERMINATED")

    def is_successful(self) -> bool:
        """Checks if the workflow has completed in successful state
        :return: True if the workflow status is COMPLETED

        Example:
            workflow = WorkflowAdapter(status="COMPLETED")
            if workflow.is_successful():
                print("Workflow completed successfully!")
        """
        return self.status == "COMPLETED"

    def is_running(self) -> bool:
        """Checks if the workflow is currently running
        :return: True if the workflow status is RUNNING or PAUSED

        Example:
            workflow = WorkflowAdapter(status="RUNNING")
            if workflow.is_running():
                print("Workflow is still executing")
        """
        return self.status in ("RUNNING", "PAUSED")

    def is_failed(self) -> bool:
        """Checks if the workflow has failed
        :return: True if the workflow status is FAILED, TIMED_OUT, or TERMINATED

        Example:
            workflow = WorkflowAdapter(status="FAILED")
            if workflow.is_failed():
                print("Workflow execution failed")
        """
        return self.status in ("FAILED", "TIMED_OUT", "TERMINATED")

    @property
    def current_task(self) -> Optional["TaskAdapter"]:
        """Gets the currently in-progress task
        :return: The task that is currently SCHEDULED or IN_PROGRESS, or None if no such task exists

        Example:
            workflow = WorkflowAdapter(tasks=[...])
            current = workflow.current_task
            if current:
                print(f"Current task: {current.task_def_name}")
        """
        if not self.tasks:
            return None
        for task in self.tasks:
            if task.status in ("SCHEDULED", "IN_PROGRESS"):
                return task
        return None

    def get_in_progress_tasks(self) -> List["TaskAdapter"]:
        """Gets all currently in-progress tasks
        :return: List of tasks that are currently SCHEDULED or IN_PROGRESS

        Example:
            workflow = WorkflowAdapter(tasks=[...])
            in_progress = workflow.get_in_progress_tasks()
            print(f"Found {len(in_progress)} in-progress tasks")
        """
        if not self.tasks:
            return []
        return [task for task in self.tasks if task.status in ("SCHEDULED", "IN_PROGRESS")]

    def get_task_by_reference_name(self, reference_name: str) -> Optional["TaskAdapter"]:
        """Gets a task by its reference name
        :param reference_name: The reference name of the task to find
        :return: The task with the specified reference name, or None if not found

        Example:
            workflow = WorkflowAdapter(tasks=[...])
            task = workflow.get_task_by_reference_name("process_data")
            if task:
                print(f"Found task: {task.task_def_name}")
        """
        if not self.tasks:
            return None
        for task in self.tasks:
            if (
                hasattr(task, "workflow_task")
                and task.workflow_task
                and hasattr(task.workflow_task, "task_reference_name")
            ):
                if task.workflow_task.task_reference_name == reference_name:
                    return task
        return None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of Workflow from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "correlationId": obj.get("correlationId"),
                "createTime": obj.get("createTime"),
                "createdBy": obj.get("createdBy"),
                "endTime": obj.get("endTime"),
                "event": obj.get("event"),
                "externalInputPayloadStoragePath": obj.get("externalInputPayloadStoragePath"),
                "externalOutputPayloadStoragePath": obj.get("externalOutputPayloadStoragePath"),
                "failedReferenceTaskNames": obj.get("failedReferenceTaskNames"),
                "failedTaskNames": obj.get("failedTaskNames"),
                "history": (
                    [WorkflowAdapter.from_dict(_item) for _item in obj["history"]]
                    if obj.get("history") is not None
                    else None
                ),
                "idempotencyKey": obj.get("idempotencyKey"),
                "input": obj.get("input"),
                "lastRetriedTime": obj.get("lastRetriedTime"),
                "output": obj.get("output"),
                "ownerApp": obj.get("ownerApp"),
                "parentWorkflowId": obj.get("parentWorkflowId"),
                "parentWorkflowTaskId": obj.get("parentWorkflowTaskId"),
                "priority": obj.get("priority"),
                "rateLimitKey": obj.get("rateLimitKey"),
                "rateLimited": obj.get("rateLimited"),
                "reRunFromWorkflowId": obj.get("reRunFromWorkflowId"),
                "reasonForIncompletion": obj.get("reasonForIncompletion"),
                "startTime": obj.get("startTime"),
                "status": obj.get("status"),
                "taskToDomain": obj.get("taskToDomain"),
                "tasks": (
                    [TaskAdapter.from_dict(_item) for _item in obj["tasks"]]
                    if obj.get("tasks") is not None
                    else None
                ),
                "updateTime": obj.get("updateTime"),
                "updatedBy": obj.get("updatedBy"),
                "variables": obj.get("variables"),
                "workflowDefinition": (
                    WorkflowDefAdapter.from_dict(obj["workflowDefinition"])
                    if obj.get("workflowDefinition") is not None
                    else None
                ),
                "workflowId": obj.get("workflowId"),
                "workflowName": obj.get("workflowName"),
                "workflowVersion": obj.get("workflowVersion"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.task_adapter import (  # noqa: E402
    TaskAdapter,
)
from conductor.asyncio_client.adapters.models.workflow_def_adapter import (  # noqa: E402
    WorkflowDefAdapter,
)

WorkflowAdapter.model_rebuild(raise_errors=False)
