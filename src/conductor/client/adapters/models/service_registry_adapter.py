from enum import Enum

from conductor.client.codegen.models.service_registry import (
    Config, OrkesCircuitBreakerConfig, ServiceRegistry)


class ServiceType(str, Enum):
    HTTP = "HTTP"
    GRPC = "gRPC"


class ServiceRegistryAdapter(ServiceRegistry):
    pass


class OrkesCircuitBreakerConfigAdapter(OrkesCircuitBreakerConfig):
    pass


class ConfigAdapter(Config):
    pass
