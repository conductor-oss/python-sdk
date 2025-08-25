from copy import deepcopy

from conductor.asyncio_client.adapters.models.workflow_task_adapter import \
    WorkflowTaskAdapter
from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType


class EventTaskInterface(TaskInterface):
    def __init__(self, task_ref_name: str, event_prefix: str, event_suffix: str):
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.EVENT,
        )
        self._sink = f"{deepcopy(event_prefix)}:{deepcopy(event_suffix)}"

    def to_workflow_task(self) -> WorkflowTaskAdapter:
        wf_task = super().to_workflow_task()
        wf_task.sink = self._sink
        return wf_task


class SqsEventTask(EventTaskInterface):
    def __init__(self, task_ref_name: str, queue_name: str):
        super().__init__(task_ref_name, "sqs", queue_name)


class ConductorEventTask(EventTaskInterface):
    def __init__(self, task_ref_name: str, event_name: str):
        super().__init__(task_ref_name, "conductor", event_name)
