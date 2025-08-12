from __future__ import annotations

from typing import Dict, Optional

from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType


class JavascriptTask(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        script: str,
        bindings: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.INLINE,
            input_parameters={
                "evaluatorType": "graaljs",
                "expression": script,
            },
        )
        if bindings:
            self.input_parameters.update(bindings)

    def output(self, json_path: Optional[str] = None) -> str:
        base_path = f"{self.task_reference_name}.output.result"
        return f"${{{base_path if json_path is None else f'{base_path}.{json_path}'}}}"

    def evaluator_type(self, evaluator_type: str):
        self.input_parameters["evaluatorType"] = evaluator_type
        return self
