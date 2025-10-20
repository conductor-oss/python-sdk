from __future__ import annotations

from typing import Optional

from deprecated import deprecated

from conductor.client.adapters.models.task_adapter import TaskAdapter
from conductor.client.codegen.models.workflow_run import WorkflowRun

terminal_status = ("COMPLETED", "FAILED", "TIMED_OUT", "TERMINATED")  # shared
successful_status = ("PAUSED", "COMPLETED")
running_status = ("RUNNING", "PAUSED")


class WorkflowRunAdapter(WorkflowRun):
    def __init__(
        self,
        correlation_id=None,
        create_time=None,
        created_by=None,
        input=None,
        output=None,
        priority=None,
        request_id=None,
        status=None,
        tasks=None,
        update_time=None,
        variables=None,
        workflow_id=None,
        reason_for_incompletion=None,
    ):
        """WorkflowRun - a model defined in Swagger"""
        self._correlation_id = None
        self._create_time = None
        self._created_by = None
        self._input = None
        self._output = None
        self._priority = None
        self._request_id = None
        self._status = None
        self._tasks = None
        self._update_time = None
        self._variables = None
        self._workflow_id = None
        self.discriminator = None
        self._reason_for_incompletion = reason_for_incompletion  # deprecated

        if correlation_id is not None:
            self.correlation_id = correlation_id
        if create_time is not None:
            self.create_time = create_time
        if created_by is not None:
            self.created_by = created_by
        if input is not None:
            self.input = input
        if output is not None:
            self.output = output
        if priority is not None:
            self.priority = priority
        if request_id is not None:
            self.request_id = request_id
        if status is not None:
            self.status = status
        if tasks is not None:
            self.tasks = tasks
        if update_time is not None:
            self.update_time = update_time
        if variables is not None:
            self.variables = variables
        if workflow_id is not None:
            self.workflow_id = workflow_id

    @property
    def current_task(self) -> TaskAdapter:
        current = None
        for task in self.tasks:
            if task.status in ("SCHEDULED", "IN_PROGRESS"):
                current = task
        return current

    def get_task(self, name: Optional[str] = None, task_reference_name: Optional[str] = None) -> TaskAdapter:
        if name is None and task_reference_name is None:
            raise Exception("ONLY one of name or task_reference_name MUST be provided.  None were provided")
        if name is not None and task_reference_name is not None:
            raise Exception("ONLY one of name or task_reference_name MUST be provided.  both were provided")

        current = None
        for task in self.tasks:
            if task.task_def_name == name or task.workflow_task.task_reference_name == task_reference_name:
                current = task
        return current

    def is_completed(self) -> bool:
        """Checks if the workflow has completed
        :return: True if the workflow status is COMPLETED, FAILED or TERMINATED
        """
        return self._status in terminal_status

    def is_successful(self) -> bool:
        """Checks if the workflow has completed in successful state (ie COMPLETED)
        :return: True if the workflow status is COMPLETED
        """
        return self._status in successful_status

    def is_running(self) -> bool:
        return self.status in running_status

    @property
    @deprecated
    def reason_for_incompletion(self):
        return self._reason_for_incompletion
