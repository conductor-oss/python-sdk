from __future__ import annotations

from typing import List, Optional

from conductor.asyncio_client.adapters.models.handled_event_response_adapter import \
    HandledEventResponseAdapter
from conductor.asyncio_client.http.models import \
    SearchResultHandledEventResponse


class SearchResultHandledEventResponseAdapter(SearchResultHandledEventResponse):
    results: Optional[List[HandledEventResponseAdapter]] = None
