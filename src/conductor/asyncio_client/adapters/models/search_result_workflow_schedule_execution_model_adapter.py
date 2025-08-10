from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import Self

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

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of SearchResultWorkflowScheduleExecutionModel from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "results": [WorkflowScheduleExecutionModelAdapter.from_dict(_item) for _item in obj["results"]] if obj.get("results") is not None else None,
            "totalHits": obj.get("totalHits")
        })
        return _obj
