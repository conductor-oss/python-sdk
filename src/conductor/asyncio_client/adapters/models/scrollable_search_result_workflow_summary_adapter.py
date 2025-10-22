from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import Self

from conductor.asyncio_client.http.models import ScrollableSearchResultWorkflowSummary


class ScrollableSearchResultWorkflowSummaryAdapter(ScrollableSearchResultWorkflowSummary):
    results: Optional[List["WorkflowSummaryAdapter"]] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of ScrollableSearchResultWorkflowSummary from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "queryId": obj.get("queryId"),
                "results": (
                    [WorkflowSummaryAdapter.from_dict(_item) for _item in obj["results"]]
                    if obj.get("results") is not None
                    else None
                ),
                "totalHits": obj.get("totalHits"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.workflow_summary_adapter import (  # noqa: E402
    WorkflowSummaryAdapter,
)

ScrollableSearchResultWorkflowSummaryAdapter.model_rebuild(raise_errors=False)
