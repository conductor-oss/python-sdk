from __future__ import annotations

from typing import Optional

from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import \
    StartWorkflowRequestAdapter
from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType


class StartWorkflowTask(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        workflow_name: str,
        start_workflow_request: StartWorkflowRequestAdapter,
        version: Optional[int] = None,
    ):
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
            },
        )
