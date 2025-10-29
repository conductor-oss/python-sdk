from typing import List, Dict

from conductor.client.codegen.api.event_resource_api import EventResourceApi
from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.http.models.event_handler import EventHandler
from conductor.client.http.models.tag import Tag
from conductor.client.http.models.connectivity_test_input import ConnectivityTestInput
from conductor.client.http.models.connectivity_test_result import ConnectivityTestResult


class EventResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = EventResourceApi(api_client)

    def add_event_handler(self, body: List[EventHandler], **kwargs) -> None:
        """Add a new event handler"""
        return self._api.add_event_handler(body, **kwargs)

    def delete_queue_config(self, queue_type: str, queue_name: str, **kwargs) -> None:
        """Delete a queue config"""
        return self._api.delete_queue_config(queue_type, queue_name, **kwargs)

    def delete_tag_for_event_handler(self, body: List[Tag], name: str, **kwargs) -> None:
        """Delete a tag for an event handler"""
        return self._api.delete_tag_for_event_handler(body, name, **kwargs)

    def get_event_handler_by_name(self, name: str, **kwargs) -> EventHandler:
        """Get an event handler by name"""
        return self._api.get_event_handler_by_name(name, **kwargs)

    def get_event_handlers(self, **kwargs) -> List[EventHandler]:
        """Get all event handlers"""
        return self._api.get_event_handlers(**kwargs)

    def get_event_handlers_for_event(self, event: str, **kwargs) -> List[EventHandler]:
        """Get event handlers for an event"""
        return self._api.get_event_handlers_for_event(event, **kwargs)

    def get_queue_config(self, queue_type: str, queue_name: str, **kwargs) -> Dict[str, object]:
        """Get a queue config"""
        return self._api.get_queue_config(queue_type, queue_name, **kwargs)

    def get_queue_names(self, **kwargs) -> Dict[str, str]:
        """Get all queue names"""
        return self._api.get_queue_names(**kwargs)

    def get_tags_for_event_handler(self, name: str, **kwargs) -> List[Tag]:
        """Get tags for an event handler"""
        return self._api.get_tags_for_event_handler(name, **kwargs)

    def handle_incoming_event(self, body: Dict[str, object], **kwargs) -> None:
        """Handle an incoming event"""
        return self._api.handle_incoming_event(body, **kwargs)

    def put_queue_config(self, body: str, queue_type: str, queue_name: str, **kwargs) -> None:
        """Put a queue config"""
        return self._api.put_queue_config(body, queue_type, queue_name, **kwargs)

    def put_tag_for_event_handler(self, body: List[Tag], name: str, **kwargs) -> None:
        """Put a tag for an event handler"""
        return self._api.put_tag_for_event_handler(body, name, **kwargs)

    def remove_event_handler_status(self, name: str, **kwargs) -> None:
        """Remove the status of an event handler"""
        return self._api.remove_event_handler_status(name, **kwargs)

    def test(self, **kwargs) -> EventHandler:
        """Test the event handler"""
        return self._api.test(**kwargs)

    def test_connectivity(self, body: ConnectivityTestInput, **kwargs) -> ConnectivityTestResult:
        """Test the connectivity of an event handler"""
        return self._api.test_connectivity(body, **kwargs)

    def update_event_handler(self, body: EventHandler, **kwargs) -> None:
        """Update an event handler"""
        return self._api.update_event_handler(body, **kwargs)
