# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Declarative Open Context Graph configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OcgConfig:
    """Configure Conductor-managed OCG integration for an agent.

    ``credential`` is the name of a Conductor secret. Raw API keys are not
    accepted or stored by this configuration.
    """

    url: str
    credential: str = "OCG_PUBLIC_KEY"
    user: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.url, str):
            raise ValueError("OcgConfig url must be a non-empty string")
        normalized_url = self.url.strip().rstrip("/")
        if not normalized_url:
            raise ValueError("OcgConfig url must be non-empty")

        if not isinstance(self.credential, str):
            raise ValueError("OcgConfig credential must be a non-empty secret name")
        normalized_credential = self.credential.strip()
        if not normalized_credential:
            raise ValueError("OcgConfig credential must be a non-empty secret name")

        object.__setattr__(self, "url", normalized_url)
        object.__setattr__(self, "credential", normalized_credential)
