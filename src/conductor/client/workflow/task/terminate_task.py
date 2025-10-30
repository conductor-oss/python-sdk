from enum import Enum

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class WorkflowStatus(str, Enum):
    COMPLETED = ("COMPLETED",)
    FAILED = ("FAILED",)
    PAUSED = ("PAUSED",)
    RUNNING = ("RUNNING",)
    TERMINATED = ("TERMINATED",)
    TIMEOUT_OUT = ("TIMED_OUT",)


class TerminateTask(TaskInterface):
    def __init__(self, task_ref_name: str, status: WorkflowStatus, termination_reason: str) -> None:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.TERMINATE,
            input_parameters={
                "terminationStatus": status,
                "terminationReason": termination_reason,
            },
        )
