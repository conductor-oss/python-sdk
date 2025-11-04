from typing import List

from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.event_execution_resource_api import EventExecutionResourceApi
from conductor.client.http.models.extended_event_execution import ExtendedEventExecution
from conductor.client.http.models.search_result_handled_event_response import (
    SearchResultHandledEventResponse,
)


class EventExecutionResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = EventExecutionResourceApi(api_client)

    def get_event_handlers_for_event1(self, **kwargs) -> SearchResultHandledEventResponse:
        """Get all active event handlers for the last 24 hours"""
        return self._api.get_event_handlers_for_event1(**kwargs)

    def get_event_handlers_for_event2(
        self, event: str, _from: str, **kwargs
    ) -> List[ExtendedEventExecution]:
        """Get event handlers for an event"""
        return self._api.get_event_handlers_for_event2(event, _from, **kwargs)
