from __future__ import annotations

from typing import Optional, List

from conductor.asyncio_client.http.models import ScrollableSearchResultWorkflowSummary
from conductor.asyncio_client.adapters.models.workflow_summary_adapter import WorkflowSummaryAdapter


class ScrollableSearchResultWorkflowSummaryAdapter(
    ScrollableSearchResultWorkflowSummary
):
    results: Optional[List[WorkflowSummaryAdapter]] = None
