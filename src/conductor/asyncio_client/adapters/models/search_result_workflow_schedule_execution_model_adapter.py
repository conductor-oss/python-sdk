from __future__ import annotations

from typing import Optional, List

from conductor.asyncio_client.http.models import SearchResultWorkflowScheduleExecutionModel
from conductor.asyncio_client.adapters.models.workflow_schedule_execution_model_adapter import WorkflowScheduleExecutionModelAdapter


class SearchResultWorkflowScheduleExecutionModelAdapter(
    SearchResultWorkflowScheduleExecutionModel
):
    results: Optional[List[WorkflowScheduleExecutionModelAdapter]] = None

