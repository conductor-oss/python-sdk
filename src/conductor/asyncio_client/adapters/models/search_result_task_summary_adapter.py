from __future__ import annotations

from typing import Optional, List

from conductor.asyncio_client.http.models import SearchResultTaskSummary
from conductor.asyncio_client.adapters.models.task_summary_adapter import TaskSummaryAdapter


class SearchResultTaskSummaryAdapter(SearchResultTaskSummary):
    results: Optional[List[TaskSummaryAdapter]] = None
