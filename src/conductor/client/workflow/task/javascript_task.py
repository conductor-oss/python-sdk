from __future__ import annotations
from typing import Dict, Optional
from typing_extensions import Self

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class JavascriptTask(TaskInterface):
    def __init__(self, task_ref_name: str, script: str, bindings: Optional[Dict[str, str]] = None) -> Self:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.INLINE,
            input_parameters={
                "evaluatorType": "graaljs",
                "expression": script,
            }
        )
        if bindings is not None:
            self.input_parameters.update(bindings)

    def output(self, json_path: Optional[str] = None) -> str:
        if json_path is None:
            return '${' + f'{self.task_reference_name}.output.result' + '}'
        else:
            return '${' + f'{self.task_reference_name}.output.result.{json_path}' + '}'

    def evaluator_type(self, evaluator_type: str) -> Self:
        self.input_parameters['evaluatorType'] = evaluator_type
        return self
