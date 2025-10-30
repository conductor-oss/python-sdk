from copy import deepcopy

from conductor.client.http.models.workflow_task import WorkflowTask
from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class EventTaskInterface(TaskInterface):
    def __init__(self, task_ref_name: str, event_prefix: str, event_suffix: str) -> None:
        super().__init__(task_reference_name=task_ref_name, task_type=TaskType.EVENT)
        self._sink = deepcopy(event_prefix) + ":" + deepcopy(event_suffix)

    def to_workflow_task(self) -> WorkflowTask:
        workflow_task = super().to_workflow_task()
        workflow_task.sink = self._sink
        return workflow_task


class SqsEventTask(EventTaskInterface):
    def __init__(self, task_ref_name: str, queue_name: str) -> None:
        super().__init__(task_ref_name, "sqs", queue_name)


class ConductorEventTask(EventTaskInterface):
    def __init__(self, task_ref_name: str, event_name: str) -> None:
        super().__init__(task_ref_name, "conductor", event_name)
