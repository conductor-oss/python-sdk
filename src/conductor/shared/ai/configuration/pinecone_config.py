from __future__ import annotations

import os
from typing import Optional

from conductor.shared.ai.configuration.interfaces.integration_config import IntegrationConfig


class PineconeConfig(IntegrationConfig):
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        environment: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> None:
        if api_key is None:
            self.api_key = os.getenv("PINECONE_API_KEY")
        else:
            self.api_key = api_key

        if endpoint is None:
            self.endpoint = os.getenv("PINECONE_ENDPOINT")
        else:
            self.endpoint = endpoint

        if environment is None:
            self.environment = os.getenv("PINECONE_ENV")
        else:
            self.environment = environment

        if project_name is None:
            self.project_name = os.getenv("PINECONE_PROJECT")
        else:
            self.project_name = project_name

    def to_dict(self) -> dict:
        return {
            "api_key": self.api_key,
            "endpoint": self.endpoint,
            "projectName": self.project_name,
            "environment": self.environment,
        }
