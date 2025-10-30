from __future__ import annotations

from typing import List, Optional

from conductor.client.adapters.models.task_adapter import TaskAdapter
from conductor.client.adapters.models.workflow_run_adapter import (
    running_status,
    successful_status,
    terminal_status,
)
from conductor.client.codegen.models.workflow import Workflow


class WorkflowAdapter(Workflow):
    def is_completed(self) -> bool:
        """Checks if the workflow has completed
        :return: True if the workflow status is COMPLETED, FAILED or TERMINATED

        Example:
            workflow = WorkflowAdapter(status="COMPLETED")
            if workflow.is_completed():
                print("Workflow has finished")
        """
        return self.status in terminal_status

    def is_successful(self) -> bool:
        """Checks if the workflow has completed in successful state (ie COMPLETED)
        :return: True if the workflow status is COMPLETED

        Example:
            workflow = WorkflowAdapter(status="COMPLETED")
            if workflow.is_successful():
                print("Workflow completed successfully!")
        """
        return self.status in successful_status

    def is_running(self) -> bool:
        """Checks if the workflow is currently running
        :return: True if the workflow status is RUNNING or PAUSED

        Example:
            workflow = WorkflowAdapter(status="RUNNING")
            if workflow.is_running():
                print("Workflow is still executing")
        """
        return self.status in running_status

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
    def current_task(self) -> Optional[TaskAdapter]:
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

    def get_in_progress_tasks(self) -> List[TaskAdapter]:
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

    def get_task_by_reference_name(self, reference_name: str) -> Optional[TaskAdapter]:
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

    def get_task(
        self, name: Optional[str] = None, task_reference_name: Optional[str] = None
    ) -> Optional[TaskAdapter]:
        """Gets a task by name or reference name (deprecated - use get_task_by_reference_name instead)
        :param name: The task definition name
        :param task_reference_name: The task reference name
        :return: The task matching the criteria, or None if not found
        """
        if name is None and task_reference_name is None:
            raise ValueError(
                "ONLY one of name or task_reference_name MUST be provided.  None were provided"
            )
        if name is not None and task_reference_name is not None:
            raise ValueError(
                "ONLY one of name or task_reference_name MUST be provided.  both were provided"
            )

        if not self.tasks:
            return None

        for task in self.tasks:
            if name is not None and task.task_def_name == name:
                return task
            if (
                task_reference_name is not None
                and hasattr(task, "workflow_task")
                and task.workflow_task
                and hasattr(task.workflow_task, "task_reference_name")
            ):
                if task.workflow_task.task_reference_name == task_reference_name:
                    return task
        return None
