from __future__ import annotations

from copy import deepcopy
from typing import Dict, List, Optional

from conductor.asyncio_client.adapters.models.workflow_task_adapter import WorkflowTaskAdapter
from conductor.asyncio_client.workflow.task.task import (
    TaskInterface,
    get_task_interface_list_as_workflow_task_list,
)
from conductor.shared.workflow.enums import EvaluatorType, TaskType


class SwitchTask(TaskInterface):
    def __init__(self, task_ref_name: str, case_expression: str, use_javascript: bool = False):
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.SWITCH,
        )
        self._default_case: Optional[List[TaskInterface]] = None
        self._decision_cases: Dict[str, List[TaskInterface]] = {}
        self._expression = deepcopy(case_expression)
        self._use_javascript = deepcopy(use_javascript)

    def switch_case(self, case_name: str, tasks: List[TaskInterface]):
        if isinstance(tasks, List):
            self._decision_cases[case_name] = deepcopy(tasks)
        else:
            self._decision_cases[case_name] = [deepcopy(tasks)]
        return self

    def default_case(self, tasks: List[TaskInterface]):
        if isinstance(tasks, List):
            self._default_case = deepcopy(tasks)
        else:
            self._default_case = [deepcopy(tasks)]
        return self

    def to_workflow_task(self) -> WorkflowTaskAdapter:
        workflow = super().to_workflow_task()
        if self._use_javascript:
            workflow.evaluator_type = EvaluatorType.ECMASCRIPT
            workflow.expression = self._expression
        else:
            workflow.evaluator_type = EvaluatorType.VALUE_PARAM
            workflow.input_parameters["switchCaseValue"] = self._expression  # type: ignore[index]
            workflow.expression = "switchCaseValue"
        workflow.decision_cases = {}
        for case_value, tasks in self._decision_cases.items():
            workflow.decision_cases[case_value] = get_task_interface_list_as_workflow_task_list(
                *tasks,
            )
        if self._default_case is None:
            self._default_case = []
        workflow.default_case = get_task_interface_list_as_workflow_task_list(*self._default_case)  # type: ignore[misc]
        return workflow
