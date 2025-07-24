from __future__ import annotations
from typing import Optional
from typing_extensions import Self

from conductor.client.http.models.start_workflow_request import StartWorkflowRequest
from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class StartWorkflowTask(TaskInterface):
    def __init__(self, task_ref_name: str, workflow_name: str, start_workflow_request: StartWorkflowRequest,
                 version: Optional[int] = None) -> Self:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.START_WORKFLOW,
            input_parameters={
                "startWorkflow": {
                    "name": workflow_name,
                    "version": version,
                    "input": start_workflow_request.input,
                    "correlationId": start_workflow_request.correlation_id,
                },
            }
        )
