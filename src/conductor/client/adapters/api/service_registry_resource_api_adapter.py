from conductor.client.codegen.api.service_registry_resource_api import ServiceRegistryResourceApi
from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from typing import List
from conductor.client.http.models.service_registry import ServiceRegistry
from conductor.client.http.models.circuit_breaker_transition_response import (
    CircuitBreakerTransitionResponse,
)
from conductor.client.http.models.service_method import ServiceMethod
from conductor.client.http.models.proto_registry_entry import ProtoRegistryEntry


class ServiceRegistryResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = ServiceRegistryResourceApi(api_client)

    def get_registered_services(self, **kwargs) -> List[ServiceRegistry]:
        """Get all registered services"""
        return self._api.get_registered_services(**kwargs)

    def remove_service(self, name: str, **kwargs) -> None:
        """Remove a service"""
        return self._api.remove_service(name, **kwargs)

    def get_service(self, name: str, **kwargs) -> ServiceRegistry:
        """Get a service"""
        return self._api.get_service(name, **kwargs)

    def open_circuit_breaker(self, name: str, **kwargs) -> CircuitBreakerTransitionResponse:
        """Open a circuit breaker"""
        return self._api.open_circuit_breaker(name, **kwargs)

    def close_circuit_breaker(self, name: str, **kwargs) -> CircuitBreakerTransitionResponse:
        """Close a circuit breaker"""
        return self._api.close_circuit_breaker(name, **kwargs)

    def get_circuit_breaker_status(self, name: str, **kwargs) -> CircuitBreakerTransitionResponse:
        """Get the status of a circuit breaker"""
        return self._api.get_circuit_breaker_status(name, **kwargs)

    def add_or_update_service(self, body: ServiceRegistry, **kwargs) -> None:
        """Add or update a service"""
        return self._api.add_or_update_service(body, **kwargs)

    def add_or_update_method(self, registry_name: str, body: ServiceMethod, **kwargs) -> None:
        """Add or update a method"""
        return self._api.add_or_update_method(registry_name, body, **kwargs)

    def remove_method(
        self, registry_name: str, service_name: str, method: str, method_type: str, **kwargs
    ) -> None:
        """Remove a method"""
        return self._api.remove_method(registry_name, service_name, method, method_type, **kwargs)

    def get_proto_data(self, registry_name: str, filename: str, **kwargs) -> bytes:
        """Get proto data"""
        return self._api.get_proto_data(registry_name, filename, **kwargs)

    def set_proto_data(self, registry_name: str, filename: str, data: bytes, **kwargs) -> None:
        """Set proto data"""
        return self._api.set_proto_data(registry_name, filename, data, **kwargs)

    def delete_proto(self, registry_name: str, filename: str, **kwargs) -> None:
        """Delete proto"""
        return self._api.delete_proto(registry_name, filename, **kwargs)

    def get_all_protos(self, registry_name: str, **kwargs) -> List[ProtoRegistryEntry]:
        """Get all protos"""
        return self._api.get_all_protos(registry_name, **kwargs)

    def discover(self, name: str, **kwargs) -> List[ServiceMethod]:
        """Discover a service"""
        return self._api.discover(name, **kwargs)
