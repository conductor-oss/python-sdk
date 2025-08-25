from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType, WorkflowStatus


class TerminateTask(TaskInterface):
    def __init__(
        self, task_ref_name: str, status: WorkflowStatus, termination_reason: str
    ):
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.TERMINATE,
            input_parameters={
                "terminationStatus": status,
                "terminationReason": termination_reason,
            },
        )
