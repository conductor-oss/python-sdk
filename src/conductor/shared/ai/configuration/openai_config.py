from __future__ import annotations

import os
from typing import Optional

from conductor.shared.ai.configuration.interfaces.integration_config import IntegrationConfig


class OpenAIConfig(IntegrationConfig):

    def __init__(self, api_key: Optional[str] = None) -> None:
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        self.api_key = api_key

    def to_dict(self) -> dict:
        return {
            "api_key": self.api_key
        }
