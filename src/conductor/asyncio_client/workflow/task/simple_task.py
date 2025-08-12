from typing import Dict

from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType


class SimpleTask(TaskInterface):
    def __init__(self, task_def_name: str, task_reference_name: str):
        super().__init__(
            task_reference_name=task_reference_name,
            task_type=TaskType.SIMPLE,
            task_name=task_def_name,
        )


def simple_task(
    task_def_name: str, task_reference_name: str, inputs: Dict[str, object]
):
    task = SimpleTask(
        task_def_name=task_def_name, task_reference_name=task_reference_name
    )
    task.input_parameters.update(inputs)
    return task
