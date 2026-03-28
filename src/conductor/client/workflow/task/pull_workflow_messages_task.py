from __future__ import annotations

from typing_extensions import Self

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class PullWorkflowMessagesTask(TaskInterface):
    """Consume messages from the workflow's message queue (WMQ).

    When messages are available the task completes with:
        output.messages  — list of WorkflowMessage objects
        output.count     — number of messages returned

    When the queue is empty the task stays IN_PROGRESS and is re-evaluated
    after ~1 second (non-blocking polling behavior).

    Args:
        task_ref_name: Unique task reference name within the workflow.
        batch_size: Maximum number of messages to dequeue per execution (default 1,
                    server cap is typically 100).
    """

    def __init__(self, task_ref_name: str, batch_size: int = 1) -> Self:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.PULL_WORKFLOW_MESSAGES,
        )
        self.input_parameters["batchSize"] = batch_size
