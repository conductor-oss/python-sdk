from __future__ import annotations

from typing import List, Optional

from conductor.asyncio_client.adapters.models.workflow_summary_adapter import (
    WorkflowSummaryAdapter,
)
from conductor.asyncio_client.http.models import ScrollableSearchResultWorkflowSummary


class ScrollableSearchResultWorkflowSummaryAdapter(
    ScrollableSearchResultWorkflowSummary
):
    results: Optional[List[WorkflowSummaryAdapter]] = None
