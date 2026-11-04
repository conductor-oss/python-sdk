from copy import deepcopy
from typing import List, Optional

from conductor.client.http.models.workflow_task import WorkflowTask
from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class ExclusiveJoinTask(TaskInterface):
    """Join the first executed branch, with optional fallback task references."""

    def __init__(
        self,
        task_ref_name: str,
        join_on: List[str],
        default_exclusive_join_task: Optional[List[str]] = None,
    ) -> None:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.EXCLUSIVE_JOIN,
        )
        self._join_on = deepcopy(join_on)
        self._default_exclusive_join_task = deepcopy(default_exclusive_join_task)

    def to_workflow_task(self) -> WorkflowTask:
        workflow = super().to_workflow_task()
        workflow.join_on = self._join_on
        workflow.default_exclusive_join_task = self._default_exclusive_join_task
        return workflow
