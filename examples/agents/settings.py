# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Shared settings for all examples.

Set ``CONDUCTOR_AGENT_LLM_MODEL`` as an environment variable to override the
default model used by all examples::

    export CONDUCTOR_AGENT_LLM_MODEL=anthropic/claude-sonnet-4-20250514
    export CONDUCTOR_AGENT_LLM_MODEL=google_gemini/gemini-2.0-flash

If unset, defaults to ``anthropic/claude-sonnet-4-6``.

``CONDUCTOR_AGENT_SECONDARY_LLM_MODEL`` provides a second model for multi-model examples
(e.g., cheap triage vs capable specialist). Defaults to ``openai/gpt-4o``.
"""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    llm_model: str = "openai/gpt-4o"
    secondary_llm_model: str = "openai/gpt-4o"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            llm_model=(
                os.environ.get("CONDUCTOR_AGENT_LLM_MODEL")
                or "openai/gpt-4o"
            ),
            secondary_llm_model=(
                os.environ.get("CONDUCTOR_AGENT_SECONDARY_LLM_MODEL")
                or "openai/gpt-4o"
            ),
        )


settings = Settings.from_env()
