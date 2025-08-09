from __future__ import annotations

from typing import List, Optional

from conductor.asyncio_client.adapters.models.task_summary_adapter import (
    TaskSummaryAdapter,
)
from conductor.asyncio_client.http.models import SearchResultTaskSummary


class SearchResultTaskSummaryAdapter(SearchResultTaskSummary):
    results: Optional[List[TaskSummaryAdapter]] = None
