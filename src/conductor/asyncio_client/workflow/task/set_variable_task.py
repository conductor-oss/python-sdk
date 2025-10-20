from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType


class SetVariableTask(TaskInterface):
    def __init__(self, task_ref_name: str):
        super().__init__(task_reference_name=task_ref_name, task_type=TaskType.SET_VARIABLE)
