from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType


class JsonJQTask(TaskInterface):
    def __init__(self, task_ref_name: str, script: str):
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.JSON_JQ_TRANSFORM,
            input_parameters={"queryExpression": script},
        )
