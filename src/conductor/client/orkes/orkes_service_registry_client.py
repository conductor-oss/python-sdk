from __future__ import annotations

from typing import List, Optional, Dict

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
        super().__init__(configuration)

    def get_registered_services(self, **kwargs) -> List[ServiceRegistry]:
        return self._service_registry_api.get_registered_services(**kwargs)

    def get_service(self, name: str, **kwargs) -> ServiceRegistry:
        return self._service_registry_api.get_service(name=name, **kwargs)

    def add_or_update_service(self, service_registry: ServiceRegistry, **kwargs) -> None:
        self._service_registry_api.add_or_update_service(body=service_registry, **kwargs)

    def remove_service(self, name: str, **kwargs) -> None:
        self._service_registry_api.remove_service(name=name, **kwargs)

    def open_circuit_breaker(self, name: str, **kwargs) -> CircuitBreakerTransitionResponse:
        return self._service_registry_api.open_circuit_breaker(name=name, **kwargs)

    def close_circuit_breaker(self, name: str, **kwargs) -> CircuitBreakerTransitionResponse:
        return self._service_registry_api.close_circuit_breaker(name=name, **kwargs)

    def get_circuit_breaker_status(self, name: str, **kwargs) -> CircuitBreakerTransitionResponse:
        return self._service_registry_api.get_circuit_breaker_status(name=name, **kwargs)

    def add_or_update_method(self, registry_name: str, method: ServiceMethod, **kwargs) -> None:
        self._service_registry_api.add_or_update_method(
            registry_name=registry_name, body=method, **kwargs
        )

    def remove_method(
        self, registry_name: str, service_name: str, method: str, method_type: str, **kwargs
    ) -> None:
        self._service_registry_api.remove_method(
            registry_name=registry_name,
            service_name=service_name,
            method=method,
            method_type=method_type,
            **kwargs,
        )

    def get_proto_data(self, registry_name: str, filename: str, **kwargs) -> bytes:
        return self._service_registry_api.get_proto_data(
            registry_name=registry_name, filename=filename, **kwargs
        )

    def set_proto_data(self, registry_name: str, filename: str, data: bytes, **kwargs) -> None:
        self._service_registry_api.set_proto_data(
            registry_name=registry_name, filename=filename, data=data, **kwargs
        )

    def delete_proto(self, registry_name: str, filename: str, **kwargs) -> None:
        self._service_registry_api.delete_proto(
            registry_name=registry_name, filename=filename, **kwargs
        )

    def get_all_protos(self, registry_name: str, **kwargs) -> List[ProtoRegistryEntry]:
        return self._service_registry_api.get_all_protos(registry_name=registry_name, **kwargs)

    def discover(self, name: str, create: Optional[bool] = False, **kwargs) -> List[ServiceMethod]:
        if create:
            kwargs.update({"create": create})
        return self._service_registry_api.discover(name=name, **kwargs)

    # Additional convenience methods can be added here if needed
    def get_queue_sizes_for_all_tasks(self, **kwargs) -> Dict[str, int]:
        """Get queue sizes for all task types"""
        return self._task_api.all(**kwargs)

    def is_circuit_breaker_open(self, name: str, **kwargs) -> bool:
        """Check if circuit breaker is open for a service"""
        status = self._service_registry_api.get_circuit_breaker_status(name=name, **kwargs)
        return bool(status.current_state and status.current_state.upper() == "OPEN")
