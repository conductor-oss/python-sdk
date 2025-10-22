from __future__ import annotations

from copy import deepcopy
from typing import List, Optional

from conductor.asyncio_client.adapters.models.workflow_task_adapter import WorkflowTaskAdapter
from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType


class JoinTask(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        join_on: Optional[List[str]] = None,
        join_on_script: Optional[str] = None,
    ):
        super().__init__(task_reference_name=task_ref_name, task_type=TaskType.JOIN)
        self._join_on = deepcopy(join_on)
        if join_on_script is not None:
            self.evaluator_type = "js"
            self.expression = join_on_script

    def to_workflow_task(self) -> WorkflowTaskAdapter:
        workflow = super().to_workflow_task()
        workflow.join_on = self._join_on
        return workflow
