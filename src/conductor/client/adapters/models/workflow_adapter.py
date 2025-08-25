from __future__ import annotations

from typing import Optional

from conductor.client.adapters.models.task_adapter import TaskAdapter
from conductor.client.adapters.models.workflow_run_adapter import (
    running_status, successful_status, terminal_status)
from conductor.client.http.models.workflow import Workflow


class WorkflowAdapter(Workflow):
    def is_completed(self) -> bool:
        """Checks if the workflow has completed
        :return: True if the workflow status is COMPLETED, FAILED or TERMINATED
        """
        return self.status in terminal_status

    def is_successful(self) -> bool:
        """Checks if the workflow has completed in successful state (ie COMPLETED)
        :return: True if the workflow status is COMPLETED
        """
        return self._status in successful_status

    def is_running(self) -> bool:
        return self.status in running_status

    @property
    def current_task(self) -> TaskAdapter:
        current = None
        for task in self.tasks:
            if task.status in ("SCHEDULED", "IN_PROGRESS"):
                current = task
        return current

    def get_task(
        self, name: Optional[str] = None, task_reference_name: Optional[str] = None
    ) -> TaskAdapter:
        if name is None and task_reference_name is None:
            raise Exception(
                "ONLY one of name or task_reference_name MUST be provided.  None were provided"
            )
        if name is not None and task_reference_name is not None:
            raise Exception(
                "ONLY one of name or task_reference_name MUST be provided.  both were provided"
            )

        current = None
        for task in self.tasks:
            if (
                task.task_def_name == name
                or task.workflow_task.task_reference_name == task_reference_name
            ):
                current = task
        return current
