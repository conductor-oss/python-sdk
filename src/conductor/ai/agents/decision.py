"""Server-executed decision tools. Provider transport and credentials stay on Conductor."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

from conductor.ai.agents.tool import ToolDef


class DecisionModelTool(ToolDef):
    """Expose a server decision provider as an agent tool without a Python worker.

    ``provider`` and ``model`` are fixed configuration, not model-generated tool
    arguments. When ``questions`` is supplied, only ``state`` is exposed to the
    orchestration model. Otherwise the caller supplies both state and questions.

    Question types are ``choice`` (named ``choices``), ``score`` (ordered
    ``scale``), and ``boolean`` (a probability). Each has ``instructions``.
    Jev-specific wire formats are translated by the server implementation.

    Requires a Conductor server supporting the ``DECISION_MODEL`` task and
    ``decision_model`` tool type. This does not register provider credentials.
    """

    def __init__(
        self,
        name: str,
        description: str,
        *,
        provider: str,
        model: str,
        questions: Optional[Dict[str, Any]] = None,
        max_calls: Optional[int] = None,
    ) -> None:
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("provider must be a nonempty server provider name")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be nonempty")
        if questions is not None and (not isinstance(questions, dict) or not questions):
            raise ValueError("questions must be a nonempty mapping when supplied")
        config: Dict[str, Any] = {"provider": provider, "model": model}
        properties: Dict[str, Any] = {
            "state": {"type": "string", "description": "Observed state to evaluate."},
        }
        required = ["state"]
        if questions is not None:
            config["questions"] = deepcopy(questions)
        else:
            properties["questions"] = {
                "type": "object",
                "minProperties": 1,
                "additionalProperties": {
                    "oneOf": [
                        _question_schema(
                            "choice",
                            "choices",
                            {
                                "type": "object",
                                "minProperties": 2,
                                "maxProperties": 255,
                                "additionalProperties": {"type": "string", "minLength": 1},
                            },
                        ),
                        _question_schema(
                            "score",
                            "scale",
                            {
                                "type": "array",
                                "minItems": 2,
                                "maxItems": 10,
                                "items": {"type": "string", "minLength": 1},
                            },
                        ),
                        _question_schema("boolean"),
                    ],
                },
            }
            required.append("questions")
        super().__init__(
            name=name,
            description=description,
            input_schema={
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
            tool_type="decision_model",
            config=config,
            max_calls=max_calls,
            retry_count=0,
        )


def _question_schema(kind: str, field: str = "", schema: Optional[dict] = None) -> dict:
    properties = {
        "type": {"type": "string", "enum": [kind]},
        "instructions": {"type": "string", "minLength": 1},
    }
    required = ["type", "instructions"]
    if field:
        properties[field] = schema
        required.append(field)
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }
