from copy import deepcopy
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from typing_extensions import Self

from conductor.client.http.models.workflow_task import WorkflowTask
from conductor.client.workflow.task.task import (
    TaskInterface,
    get_task_interface_list_as_workflow_task_list,
)
from conductor.client.workflow.task.task_type import TaskType


class EvaluatorType(str, Enum):
    JAVASCRIPT = ("javascript",)
    ECMASCRIPT = ("graaljs",)
    VALUE_PARAM = "value-param"
    DECISION = "decision"


class SwitchTask(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        case_expression: str,
        use_javascript: bool = False,
        *,
        evaluator_type: Optional[Union[EvaluatorType, str]] = None,
        input_parameters: Optional[Dict[str, Any]] = None,
    ) -> Self:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.SWITCH,
            input_parameters=input_parameters,
        )
        if use_javascript and evaluator_type is not None:
            raise ValueError("use_javascript and evaluator_type cannot both be set")
        self._default_case = None
        self._decision_cases = {}
        self._expression = deepcopy(case_expression)
        self._use_javascript = deepcopy(use_javascript)
        self._switch_evaluator_type = deepcopy(evaluator_type)

    def switch_case(self, case_name: str, tasks: List[TaskInterface]) -> Self:
        if isinstance(tasks, List):
            self._decision_cases[case_name] = deepcopy(tasks)
        else:
            self._decision_cases[case_name] = [deepcopy(tasks)]
        return self

    def default_case(self, tasks: List[TaskInterface]) -> Self:
        if isinstance(tasks, List):
            self._default_case = deepcopy(tasks)
        else:
            self._default_case = [deepcopy(tasks)]
        return self

    def to_workflow_task(self) -> WorkflowTask:
        workflow = super().to_workflow_task()
        if self._switch_evaluator_type is not None:
            workflow.evaluator_type = (
                self._switch_evaluator_type.value
                if isinstance(self._switch_evaluator_type, EvaluatorType)
                else self._switch_evaluator_type
            )
            workflow.expression = self._expression
        elif self._use_javascript:
            workflow.evaluator_type = EvaluatorType.ECMASCRIPT
            workflow.expression = self._expression
        else:
            workflow.evaluator_type = EvaluatorType.VALUE_PARAM
            workflow.input_parameters["switchCaseValue"] = self._expression
            workflow.expression = "switchCaseValue"
        workflow.decision_cases = {}
        for case_value, tasks in self._decision_cases.items():
            workflow.decision_cases[case_value] = get_task_interface_list_as_workflow_task_list(
                *tasks,
            )
        if self._default_case is None:
            self._default_case = []
        workflow.default_case = get_task_interface_list_as_workflow_task_list(*self._default_case)
        return workflow
