from typing import Any

from conductor.asyncio_client.adapters.models.workflow_task_adapter import WorkflowTaskAdapter
from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType


class DynamicTask(TaskInterface):
    def __init__(
        self,
        dynamic_task: Any,
        task_reference_name: str,
        dynamic_task_param: str = "taskToExecute",
    ):
        super().__init__(
            task_reference_name=task_reference_name,
            task_type=TaskType.DYNAMIC,
            task_name="dynamic_task",
        )
        self.input_parameters[dynamic_task_param] = dynamic_task
        self._dynamic_task_param = dynamic_task_param

    def to_workflow_task(self) -> WorkflowTaskAdapter:
        wf_task = super().to_workflow_task()
        wf_task.dynamic_task_name_param = self._dynamic_task_param
        return wf_task
