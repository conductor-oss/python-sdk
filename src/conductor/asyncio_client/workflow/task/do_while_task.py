from __future__ import annotations

from copy import deepcopy
from typing import List, Optional, Sequence, Union

from conductor.asyncio_client.adapters.models.workflow_task_adapter import WorkflowTaskAdapter
from conductor.asyncio_client.workflow.task.task import (
    TaskInterface,
    get_task_interface_list_as_workflow_task_list,
)
from conductor.shared.workflow.enums import TaskType


def get_for_loop_condition(task_ref_name: str, iterations: int) -> str:
    return f"if ( $.{task_ref_name}.iteration < {iterations} ) {{ true; }} else {{ false; }}"


class DoWhileTask(TaskInterface):
    def __init__(self, task_ref_name: str, termination_condition: str, tasks: List[TaskInterface]):
        super().__init__(task_reference_name=task_ref_name, task_type=TaskType.DO_WHILE)
        self._loop_condition = str(termination_condition)
        self._loop_over: List[TaskInterface] = (
            deepcopy(list(tasks)) if isinstance(tasks, Sequence) else [deepcopy(tasks)]
        )

    def to_workflow_task(self) -> WorkflowTaskAdapter:
        workflow_task = super().to_workflow_task()
        workflow_task.loop_condition = self._loop_condition
        workflow_task.loop_over = get_task_interface_list_as_workflow_task_list(*self._loop_over)
        return workflow_task


class LoopTask(DoWhileTask):
    def __init__(
        self,
        task_ref_name: str,
        iterations: int,
        tasks: Union[TaskInterface, Sequence[TaskInterface]],
    ):
        super().__init__(
            task_ref_name=task_ref_name,
            termination_condition=get_for_loop_condition(task_ref_name, iterations),
            tasks=tasks,
        )


class ForEachTask(DoWhileTask):
    def __init__(
        self,
        task_ref_name: str,
        tasks: Union[TaskInterface, Sequence[TaskInterface]],
        iterate_over: str,
        variables: Optional[Sequence[str]] = None,
    ):
        super().__init__(
            task_ref_name=task_ref_name,
            termination_condition=get_for_loop_condition(task_ref_name, 0),
            tasks=tasks,
        )
        self.input_parameter("items", iterate_over)
        if variables is not None:
            self.input_parameter("variables", list(variables))
