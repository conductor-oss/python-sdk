# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Per-run LLM overrides for :meth:`AgentRuntime.run` / :meth:`AgentRuntime.start`.

``RunSettings`` lets a single invocation override the LLM settings baked into an
:class:`Agent` (model, temperature, …) without constructing a new agent. Only the
fields you set override; unset fields (``None``) keep the agent's own values.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RunSettings:
    """Per-invocation LLM overrides applied on top of an :class:`Agent`'s settings.

    Pass via the ``run_settings=`` keyword of ``run``/``start`` (and their async
    variants). Only non-``None`` fields override the agent; everything else is
    left as the agent defined it.

    Attributes:
        model: Provider/model id (e.g. ``"openai/gpt-4o"``).
        temperature: Sampling temperature.
        max_tokens: Maximum tokens for the completion.
        reasoning_effort: Reasoning effort for reasoning models (e.g. ``"high"``).
        thinking_budget_tokens: Extended-thinking token budget (enables thinking).
    """

    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    reasoning_effort: Optional[str] = None
    thinking_budget_tokens: Optional[int] = None

    def to_config_overrides(self) -> Dict[str, Any]:
        """Map the set fields to ``agentConfig`` wire keys.

        Mirrors :class:`~conductor.ai.agents.config_serializer.AgentConfigSerializer`
        so the wire-key names live in one place. Uses ``is not None`` so
        ``temperature=0.0`` and ``max_tokens=0`` are honored (they are falsy).
        """
        overrides: Dict[str, Any] = {}
        if self.model is not None:
            overrides["model"] = self.model
        if self.temperature is not None:
            overrides["temperature"] = self.temperature
        if self.max_tokens is not None:
            overrides["maxTokens"] = self.max_tokens
        if self.reasoning_effort is not None:
            overrides["reasoningEffort"] = self.reasoning_effort
        if self.thinking_budget_tokens is not None:
            overrides["thinkingConfig"] = {
                "enabled": True,
                "budgetTokens": self.thinking_budget_tokens,
            }
        return overrides

    @classmethod
    def coerce(cls, obj: Any) -> Optional["RunSettings"]:
        """Normalise ``None`` / a :class:`RunSettings` / a plain dict to RunSettings.

        A dict is expanded as keyword args, so unknown keys raise ``TypeError``
        (the intended minimal validation). Value validation (model names,
        ranges) is left to the server.
        """
        if obj is None:
            return None
        if isinstance(obj, RunSettings):
            return obj
        if isinstance(obj, dict):
            return cls(**obj)
        raise TypeError(
            f"run_settings must be a RunSettings or dict, got {type(obj).__name__}"
        )
