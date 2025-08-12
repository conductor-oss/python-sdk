from __future__ import annotations

from conductor.shared.ai.configuration.interfaces.integration_config import IntegrationConfig


class WeaviateConfig(IntegrationConfig):

    def __init__(self, api_key: str, endpoint: str, classname: str) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.classname = classname

    def to_dict(self) -> dict:
        return {
            "api_key": self.api_key,
            "endpoint": self.endpoint
        }
