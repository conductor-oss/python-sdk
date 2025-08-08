from __future__ import annotations

from typing import Optional

from conductor.asyncio_client.adapters.models.task_details_adapter import TaskDetailsAdapter
from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import StartWorkflowRequestAdapter
from conductor.asyncio_client.adapters.models.terminate_workflow_adapter import TerminateWorkflowAdapter
from conductor.asyncio_client.adapters.models.update_workflow_variables_adapter import UpdateWorkflowVariablesAdapter
from conductor.asyncio_client.http.models import Action


class ActionAdapter(Action):
    complete_task: Optional[TaskDetailsAdapter] = None
    fail_task: Optional[TaskDetailsAdapter] = None
    start_workflow: Optional[StartWorkflowRequestAdapter] = None
    terminate_workflow: Optional[TerminateWorkflowAdapter] = None
    update_workflow_variables: Optional[UpdateWorkflowVariablesAdapter] = None
