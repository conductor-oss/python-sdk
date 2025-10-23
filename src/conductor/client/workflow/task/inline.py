from __future__ import annotations

from typing import Dict, Optional

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class InlineTask(TaskInterface):
    def __init__(
        self, task_ref_name: str, script: str, bindings: Optional[Dict[str, str]] = None
    ) -> None:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.INLINE,
            input_parameters={
                "evaluatorType": "graaljs",
                "expression": script,
            },
        )
        if bindings is not None:
            self.input_parameters.update(bindings)
