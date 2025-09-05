from conductor.client.adapters.models.service_registry_adapter import (
    Config, OrkesCircuitBreakerConfig, ServiceRegistryAdapter, ServiceType)

ServiceRegistry = ServiceRegistryAdapter

__all__ = ["ServiceRegistry", "OrkesCircuitBreakerConfig", "Config", "ServiceType"]
