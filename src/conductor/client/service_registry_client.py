from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List

from conductor.client.adapters.models.service_registry_adapter import ServiceRegistryAdapter as ServiceRegistry
from conductor.client.adapters.models.service_method_adapter import ServiceMethodAdapter as ServiceMethod
from conductor.client.adapters.models.proto_registry_entry_adapter import ProtoRegistryEntryAdapter as ProtoRegistryEntry
from conductor.client.adapters.models.circuit_breaker_transition_response_adapter import CircuitBreakerTransitionResponseAdapter as CircuitBreakerTransitionResponse


class ServiceRegistryClient(ABC):
    @abstractmethod
    def get_registered_services(self) -> List[ServiceRegistry]:
        pass

    @abstractmethod
    def get_service(self, name: str) -> ServiceRegistry:
        pass

    @abstractmethod
    def add_or_update_service(self, service_registry: ServiceRegistry) -> None:
        pass

    @abstractmethod
    def remove_service(self, name: str) -> None:
        pass

    @abstractmethod
    def open_circuit_breaker(self, name: str) -> CircuitBreakerTransitionResponse:
        pass

    @abstractmethod
    def close_circuit_breaker(self, name: str) -> CircuitBreakerTransitionResponse:
        pass

    @abstractmethod
    def get_circuit_breaker_status(self, name: str) -> CircuitBreakerTransitionResponse:
        pass

    @abstractmethod
    def add_or_update_method(self, registry_name: str, method: ServiceMethod) -> None:
        pass

    @abstractmethod
    def remove_method(self, registry_name: str, service_name: str, method: str, method_type: str) -> None:
        pass

    @abstractmethod
    def get_proto_data(self, registry_name: str, filename: str) -> bytes:
        pass

    @abstractmethod
    def set_proto_data(self, registry_name: str, filename: str, data: bytes) -> None:
        pass

    @abstractmethod
    def delete_proto(self, registry_name: str, filename: str) -> None:
        pass

    @abstractmethod
    def get_all_protos(self, registry_name: str) -> List[ProtoRegistryEntry]:
        pass

    @abstractmethod
    def discover(self, name: str, create: Optional[bool] = False) -> List[ServiceMethod]:
        pass
