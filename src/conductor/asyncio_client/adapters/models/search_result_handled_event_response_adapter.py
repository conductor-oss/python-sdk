from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import Self

from conductor.asyncio_client.http.models import SearchResultHandledEventResponse


class SearchResultHandledEventResponseAdapter(SearchResultHandledEventResponse):
    results: Optional[List["HandledEventResponseAdapter"]] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of SearchResultHandledEventResponse from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "results": (
                    [
                        HandledEventResponseAdapter.from_dict(_item)
                        for _item in obj["results"]
                    ]
                    if obj.get("results") is not None
                    else None
                ),
                "totalHits": obj.get("totalHits"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.handled_event_response_adapter import (  # noqa: E402
    HandledEventResponseAdapter,
)

SearchResultHandledEventResponseAdapter.model_rebuild(raise_errors=False)
