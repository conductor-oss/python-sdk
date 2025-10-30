from __future__ import annotations

from conductor.shared.ai.configuration.interfaces.integration_config import IntegrationConfig


class AzureOpenAIConfig(IntegrationConfig):
    def __init__(self, api_key: str, endpoint: str) -> None:
        self.api_key = api_key
        self.endpoint = endpoint

    def to_dict(self) -> dict:
        return {"api_key": self.api_key, "endpoint": self.endpoint}
