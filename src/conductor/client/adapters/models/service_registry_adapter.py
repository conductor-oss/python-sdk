from conductor.client.http.models.service_registry import (
    Config, OrkesCircuitBreakerConfig, ServiceRegistry)


class ServiceRegistryAdapter(ServiceRegistry):
    pass


class OrkesCircuitBreakerConfigAdapter(OrkesCircuitBreakerConfig):
    pass


class ConfigAdapter(Config):
    pass
