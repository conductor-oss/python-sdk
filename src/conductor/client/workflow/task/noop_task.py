from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class NoopTask(TaskInterface):
    """A system task that completes immediately without running a worker."""

    def __init__(self, task_ref_name: str) -> None:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.NOOP,
        )
