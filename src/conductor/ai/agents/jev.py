"""Jev agent definitions. Inference and credentials stay on Conductor."""

from copy import deepcopy
from typing import Any, Dict, Optional

from conductor.ai.agents.agent import Agent


class JevAgent(Agent):
    """Supply questions here or through context.questions at runtime."""

    kind = "jev"

    def __init__(
        self,
        name: str,
        *,
        model: str,
        questions: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(name=name, model=model, metadata=metadata)
        self.questions = deepcopy(questions)
