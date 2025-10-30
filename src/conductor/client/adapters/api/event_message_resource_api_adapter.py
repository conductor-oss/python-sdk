from typing import List

from conductor.client.codegen.api.event_message_resource_api import EventMessageResourceApi
from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.http.models.search_result_handled_event_response import (
    SearchResultHandledEventResponse,
)
from conductor.client.http.models.event_message import EventMessage


class EventMessageResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = EventMessageResourceApi(api_client)

    def get_events(self, **kwargs) -> SearchResultHandledEventResponse:
        """Get all event handlers with statistics"""
        return self._api.get_events(**kwargs)

    def get_messages(self, event: str, **kwargs) -> List[EventMessage]:
        """Get messages for an event"""
        return self._api.get_messages(event, **kwargs)
