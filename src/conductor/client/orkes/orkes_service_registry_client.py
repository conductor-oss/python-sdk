from __future__ import annotations

from typing import Dict, List, Optional

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
        """Initialize the OrkesServiceRegistryClient with configuration.

        Args:
            configuration: Configuration object containing server settings and authentication

        Example:
            ```python
            from conductor.client.configuration.configuration import Configuration

            config = Configuration(server_api_url="http://localhost:8080/api")
            service_registry_client = OrkesServiceRegistryClient(config)
            ```
        """
        super().__init__(configuration)

    def get_registered_services(self, **kwargs) -> List[ServiceRegistry]:
        """Get all registered services.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of ServiceRegistry instances

        Example:
            ```python
            services = service_registry_client.get_registered_services()
            for service in services:
                print(f"Service: {service.name}, Host: {service.host}")
            ```
        """
        return self._service_registry_api.get_registered_services(**kwargs)

    def get_service(self, name: str, **kwargs) -> ServiceRegistry:
        """Get a specific service by name.

        Args:
            name: Name of the service to retrieve
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ServiceRegistry instance

        Example:
            ```python
            service = service_registry_client.get_service("payment-service")
            print(f"Service: {service.name}, Port: {service.port}")
            ```
        """
        return self._service_registry_api.get_service(name=name, **kwargs)

    def add_or_update_service(self, service_registry: ServiceRegistry, **kwargs) -> None:
        """Add or update a service in the registry.

        Args:
            service_registry: Service configuration to register
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.service_registry import ServiceRegistry

            service = ServiceRegistry(
                name="payment-service",
                host="payment.example.com",
                port=8080,
                protocol="https"
            )
            service_registry_client.add_or_update_service(service)
            ```
        """
        self._service_registry_api.add_or_update_service(body=service_registry, **kwargs)

    def remove_service(self, name: str, **kwargs) -> None:
        """Remove a service from the registry.

        Args:
            name: Name of the service to remove
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            service_registry_client.remove_service("old-payment-service")
            ```
        """
        self._service_registry_api.remove_service(name=name, **kwargs)

    def open_circuit_breaker(self, name: str, **kwargs) -> CircuitBreakerTransitionResponse:
        """Open the circuit breaker for a service.

        Args:
            name: Name of the service
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            CircuitBreakerTransitionResponse with the transition details

        Example:
            ```python
            response = service_registry_client.open_circuit_breaker("payment-service")
            print(f"Circuit breaker state: {response.current_state}")
            ```
        """
        return self._service_registry_api.open_circuit_breaker(name=name, **kwargs)

    def close_circuit_breaker(self, name: str, **kwargs) -> CircuitBreakerTransitionResponse:
        """Close the circuit breaker for a service.

        Args:
            name: Name of the service
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            CircuitBreakerTransitionResponse with the transition details

        Example:
            ```python
            response = service_registry_client.close_circuit_breaker("payment-service")
            print(f"Circuit breaker state: {response.current_state}")
            ```
        """
        return self._service_registry_api.close_circuit_breaker(name=name, **kwargs)

    def get_circuit_breaker_status(self, name: str, **kwargs) -> CircuitBreakerTransitionResponse:
        """Get the circuit breaker status for a service.

        Args:
            name: Name of the service
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            CircuitBreakerTransitionResponse with the current status

        Example:
            ```python
            status = service_registry_client.get_circuit_breaker_status("payment-service")
            print(f"Circuit breaker state: {status.current_state}")
            ```
        """
        return self._service_registry_api.get_circuit_breaker_status(name=name, **kwargs)

    def add_or_update_method(self, registry_name: str, method: ServiceMethod, **kwargs) -> None:
        """Add or update a method for a registered service.

        Args:
            registry_name: Name of the service registry
            method: Service method configuration
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.service_method import ServiceMethod

            method = ServiceMethod(
                name="processPayment",
                service_name="payment-service",
                method_type="POST"
            )
            service_registry_client.add_or_update_method("payment-registry", method)
            ```
        """
        self._service_registry_api.add_or_update_method(
            registry_name=registry_name, body=method, **kwargs
        )

    def remove_method(
        self, registry_name: str, service_name: str, method: str, method_type: str, **kwargs
    ) -> None:
        """Remove a method from a registered service.

        Args:
            registry_name: Name of the service registry
            service_name: Name of the service
            method: Name of the method to remove
            method_type: Type of the method (e.g., "POST", "GET")
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            service_registry_client.remove_method(
                "payment-registry",
                "payment-service",
                "processPayment",
                "POST"
            )
            ```
        """
        self._service_registry_api.remove_method(
            registry_name=registry_name,
            service_name=service_name,
            method=method,
            method_type=method_type,
            **kwargs,
        )

    def get_proto_data(self, registry_name: str, filename: str, **kwargs) -> bytes:
        """Get Protocol Buffer data for a service.

        Args:
            registry_name: Name of the service registry
            filename: Name of the proto file
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Proto data as bytes

        Example:
            ```python
            proto_data = service_registry_client.get_proto_data(
                "payment-registry",
                "payment.proto"
            )
            ```
        """
        return self._service_registry_api.get_proto_data(
            registry_name=registry_name, filename=filename, **kwargs
        )

    def set_proto_data(self, registry_name: str, filename: str, data: bytes, **kwargs) -> None:
        """Set Protocol Buffer data for a service.

        Args:
            registry_name: Name of the service registry
            filename: Name of the proto file
            data: Proto data as bytes
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            with open("payment.proto", "rb") as f:
                proto_data = f.read()

            service_registry_client.set_proto_data(
                "payment-registry",
                "payment.proto",
                proto_data
            )
            ```
        """
        self._service_registry_api.set_proto_data(
            registry_name=registry_name, filename=filename, data=data, **kwargs
        )

    def delete_proto(self, registry_name: str, filename: str, **kwargs) -> None:
        """Delete Protocol Buffer data for a service.

        Args:
            registry_name: Name of the service registry
            filename: Name of the proto file to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            service_registry_client.delete_proto("payment-registry", "old_payment.proto")
            ```
        """
        self._service_registry_api.delete_proto(
            registry_name=registry_name, filename=filename, **kwargs
        )

    def get_all_protos(self, registry_name: str, **kwargs) -> List[ProtoRegistryEntry]:
        """Get all Protocol Buffer entries for a registry.

        Args:
            registry_name: Name of the service registry
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of ProtoRegistryEntry instances

        Example:
            ```python
            protos = service_registry_client.get_all_protos("payment-registry")
            for proto in protos:
                print(f"Proto: {proto.filename}, Size: {len(proto.data)} bytes")
            ```
        """
        return self._service_registry_api.get_all_protos(registry_name=registry_name, **kwargs)

    def discover(self, name: str, create: Optional[bool] = False, **kwargs) -> List[ServiceMethod]:
        """Discover methods for a service.

        Args:
            name: Name of the service to discover
            create: If True, create the service if it doesn't exist
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of ServiceMethod instances

        Example:
            ```python
            methods = service_registry_client.discover("payment-service", create=True)
            for method in methods:
                print(f"Method: {method.name}, Type: {method.method_type}")
            ```
        """
        if create:
            kwargs.update({"create": create})
        return self._service_registry_api.discover(name=name, **kwargs)

    # Additional convenience methods can be added here if needed
    def get_queue_sizes_for_all_tasks(self, **kwargs) -> Dict[str, int]:
        """Get queue sizes for all task types.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping task types to queue sizes

        Example:
            ```python
            queue_sizes = service_registry_client.get_queue_sizes_for_all_tasks()
            for task_type, size in queue_sizes.items():
                print(f"Task: {task_type}, Queue Size: {size}")
            ```
        """
        return self._task_api.all(**kwargs)

    def is_circuit_breaker_open(self, name: str, **kwargs) -> bool:
        """Check if circuit breaker is open for a service.

        Args:
            name: Name of the service
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            True if circuit breaker is open, False otherwise

        Example:
            ```python
            if service_registry_client.is_circuit_breaker_open("payment-service"):
                print("Circuit breaker is open - service is unavailable")
            else:
                print("Circuit breaker is closed - service is available")
            ```
        """
        status = self._service_registry_api.get_circuit_breaker_status(name=name, **kwargs)
        return bool(status.current_state and status.current_state.upper() == "OPEN")
