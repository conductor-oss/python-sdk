from __future__ import annotations

from typing import List, Optional

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.circuit_breaker_transition_response import (
    CircuitBreakerTransitionResponse,
)
from conductor.client.http.models.proto_registry_entry import ProtoRegistryEntry
from conductor.client.http.models.service_method import ServiceMethod
from conductor.client.http.models.service_registry import ServiceRegistry
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.service_registry_client import ServiceRegistryClient


class OrkesServiceRegistryClient(OrkesBaseClient, ServiceRegistryClient):
    def __init__(self, configuration: Configuration):
        super(OrkesServiceRegistryClient, self).__init__(configuration)

    def get_registered_services(self) -> List[ServiceRegistry]:
        return self._service_registry_api.get_registered_services()

    def get_service(self, name: str) -> ServiceRegistry:
        return self._service_registry_api.get_service(name)

    def add_or_update_service(self, service_registry: ServiceRegistry) -> None:
        self._service_registry_api.add_or_update_service(service_registry)

    def remove_service(self, name: str) -> None:
        self._service_registry_api.remove_service(name)

    def open_circuit_breaker(self, name: str) -> CircuitBreakerTransitionResponse:
        return self._service_registry_api.open_circuit_breaker(name)

    def close_circuit_breaker(self, name: str) -> CircuitBreakerTransitionResponse:
        return self._service_registry_api.close_circuit_breaker(name)

    def get_circuit_breaker_status(self, name: str) -> CircuitBreakerTransitionResponse:
        return self._service_registry_api.get_circuit_breaker_status(name)

    def add_or_update_method(self, registry_name: str, method: ServiceMethod) -> None:
        self._service_registry_api.add_or_update_method(registry_name, method)

    def remove_method(
        self, registry_name: str, service_name: str, method: str, method_type: str
    ) -> None:
        self._service_registry_api.remove_method(registry_name, service_name, method, method_type)

    def get_proto_data(self, registry_name: str, filename: str) -> bytes:
        return self._service_registry_api.get_proto_data(registry_name, filename)

    def set_proto_data(self, registry_name: str, filename: str, data: bytes) -> None:
        self._service_registry_api.set_proto_data(registry_name, filename, data)

    def delete_proto(self, registry_name: str, filename: str) -> None:
        self._service_registry_api.delete_proto(registry_name, filename)

    def get_all_protos(self, registry_name: str) -> List[ProtoRegistryEntry]:
        return self._service_registry_api.get_all_protos(registry_name)

    def discover(self, name: str, create: Optional[bool] = False) -> List[ServiceMethod]:
        kwargs = {}
        if create:
            kwargs.update({"create": create})
        return self._service_registry_api.discover(name, **kwargs)

    # Additional convenience methods can be added here if needed
    def get_queue_sizes_for_all_tasks(self) -> dict:
        """Get queue sizes for all task types"""
        return self._task_api.all()

    def is_circuit_breaker_open(self, name: str) -> bool:
        """Check if circuit breaker is open for a service"""
        status = self._service_registry_api.get_circuit_breaker_status(name)
        return bool(status.current_state and status.current_state.upper() == "OPEN")
