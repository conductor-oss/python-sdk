from __future__ import annotations

from typing import Optional, List

from conductor.asyncio_client.http.models import SearchResultHandledEventResponse
from conductor.asyncio_client.adapters.models.handled_event_response_adapter import HandledEventResponseAdapter


class SearchResultHandledEventResponseAdapter(SearchResultHandledEventResponse):
    results: Optional[List[HandledEventResponseAdapter]] = None
