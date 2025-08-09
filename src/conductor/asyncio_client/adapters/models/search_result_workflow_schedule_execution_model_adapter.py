from __future__ import annotations

from typing import List, Optional

from conductor.asyncio_client.adapters.models.workflow_schedule_execution_model_adapter import (
    WorkflowScheduleExecutionModelAdapter,
)
from conductor.asyncio_client.http.models import (
    SearchResultWorkflowScheduleExecutionModel,
)


class SearchResultWorkflowScheduleExecutionModelAdapter(
    SearchResultWorkflowScheduleExecutionModel
):
    results: Optional[List[WorkflowScheduleExecutionModelAdapter]] = None
