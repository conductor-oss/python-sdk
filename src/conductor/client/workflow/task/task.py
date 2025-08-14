from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Union, Optional

from typing_extensions import Self

from conductor.client.http.models.workflow_task import WorkflowTask, CacheConfig
from conductor.client.workflow.task.task_type import TaskType


def get_task_interface_list_as_workflow_task_list(*tasks: Self) -> List[WorkflowTask]:
    converted_tasks = []
    for task in tasks:
        wf_task = task.to_workflow_task()
        if isinstance(wf_task, list):
            # to_workflow_task() returned a list. E.g.: DynamicFork.to_workflow_task() returns the DynamicFork and the Join task.
            converted_tasks.extend(wf_task)
        else:
            converted_tasks.append(task.to_workflow_task())
    return converted_tasks


class TaskInterface():
    def __init__(self,
                 task_reference_name: str,
                 task_type: TaskType,
                 task_name: Optional[str] = None,
                 description: Optional[str] = None,
                 optional: Optional[bool] = None,
                 input_parameters: Optional[Dict[str, Any]] = None,
                 cache_key: Optional[str] = None,
                 cache_ttl_second: int = 0) -> Self:
        self.task_reference_name = task_reference_name
        self.task_type = task_type
        self.task_name = task_name if task_name is not None else task_type.value
        self.description = description
        self.optional = optional
        self.input_parameters = input_parameters if input_parameters is not None else {}
        self.cache_key = cache_key
        self.cache_ttl_second = cache_ttl_second
        self._expression = None
        self._evaluator_type = None

    @property
    def task_reference_name(self) -> str:
        return self._task_reference_name

    @task_reference_name.setter
    def task_reference_name(self, task_reference_name: str) -> None:
        if not isinstance(task_reference_name, str):
            raise Exception("invalid type")
        self._task_reference_name = deepcopy(task_reference_name)

    @property
    def task_type(self) -> TaskType:
        return self._task_type

    @task_type.setter
    def task_type(self, task_type: TaskType) -> None:
        if not isinstance(task_type, TaskType):
            raise Exception("invalid type")
        self._task_type = deepcopy(task_type)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        if not isinstance(name, str):
            raise Exception("invalid type")
        self._name = name

    @property
    def expression(self) -> str:
        return self._expression

    @expression.setter
    def expression(self, expression: str) -> None:
        self._expression = expression

    @property
    def evaluator_type(self) -> str:
        return self._evaluator_type

    @evaluator_type.setter
    def evaluator_type(self, evaluator_type: str) -> None:
        self._evaluator_type = evaluator_type

    def cache(self, cache_key: str, cache_ttl_second: int):
        self._cache_key = cache_key
        self._cache_ttl_second = cache_ttl_second

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, description: str) -> None:
        if description is not None and not isinstance(description, str):
            raise Exception("invalid type")
        self._description = deepcopy(description)

    @property
    def optional(self) -> bool:
        return self._optional

    @optional.setter
    def optional(self, optional: bool) -> None:
        if optional is not None and not isinstance(optional, bool):
            raise Exception("invalid type")
        self._optional = deepcopy(optional)

    @property
    def input_parameters(self) -> Dict[str, Any]:
        return self._input_parameters

    @input_parameters.setter
    def input_parameters(self, input_parameters: Dict[str, Any]) -> None:
        if input_parameters is None:
            self._input_parameters = {}
            return
        if not isinstance(input_parameters, dict):
            try:
                self._input_parameters = input_parameters.__dict__
            except AttributeError as err:
                raise ValueError(f"Invalid type: {type(input_parameters)}") from err

        self._input_parameters = deepcopy(input_parameters)

    def input_parameter(self, key: str, value: Any) -> Self:
        if not isinstance(key, str):
            raise Exception("invalid type")
        self._input_parameters[key] = deepcopy(value)
        return self

    def to_workflow_task(self) -> WorkflowTask:
        cache_config = None
        if self.cache_ttl_second > 0 and self.cache_key is not None:
            cache_config = CacheConfig(key=self.cache_key, ttl_in_second=self.cache_ttl_second)
        return WorkflowTask(
            name=self._name,
            task_reference_name=self._task_reference_name,
            type=self._task_type.value,
            description=self._description,
            input_parameters=self._input_parameters,
            optional=self._optional,
            cache_config=cache_config,
            expression=self._expression,
            evaluator_type=self._evaluator_type
        )

    def output(self, json_path: Optional[str] = None) -> str:
        if json_path is None:
            return "${" + f"{self.task_reference_name}.output" + "}"
        elif json_path.startswith("."):
            return "${" + f"{self.task_reference_name}.output{json_path}" + "}"
        else:
            return "${" + f"{self.task_reference_name}.output.{json_path}" + "}"

    def input(self, json_path: Optional[str] = None, key: Optional[str] = None, value: Optional[Any] = None) -> Union[str, Self]:
        if key is not None and value is not None:
            """
            Set input parameter
            """
            self.input_parameters[key] = value
            return self
        else:
            """
            Get input parameter
            """
            if json_path is None:
                return "${" + f"{self.task_reference_name}.input" + "}"
            else:
                return "${" + f"{self.task_reference_name}.input.{json_path}" + "}"

    def __getattribute__(self, __name: str, /) -> Any:
        try:
            val = super().__getattribute__(__name)
            return val
        except AttributeError as ae:
            if not __name.startswith("_"):
                return "${" + self.task_reference_name + ".output." + __name + "}"
            raise ae
