"""Server-executed Jev agents. Provider transport and credentials stay on Conductor."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Optional, Sequence

from conductor.ai.agents.agent import Agent

_MIN_OPTIONS = 2
_MAX_CHOICES = 255
_MAX_SCORE_LABELS = 10


@dataclass(frozen=True)
class ChoiceQuestion:
    instructions: str
    choices: Mapping[str, str]
    type: str = "choice"


@dataclass(frozen=True)
class ScoreQuestion:
    instructions: str
    scale: Sequence[str]
    type: str = "score"


@dataclass(frozen=True)
class BooleanQuestion:
    instructions: str
    type: str = "boolean"


def jev_questions(questions: Mapping[str, Any]) -> dict:
    """Validate the typed question contract before registering or executing an agent."""
    if not isinstance(questions, Mapping) or not questions:
        raise ValueError("questions must be a nonempty mapping")
    result = {}
    for name, question in questions.items():
        q = (
            asdict(question)
            if isinstance(question, (ChoiceQuestion, ScoreQuestion, BooleanQuestion))
            else deepcopy(question)
        )
        if not isinstance(name, str) or not name.strip() or not isinstance(q, dict):
            raise ValueError("invalid Jev question")
        kind = q.get("type")
        fields = {"type", "instructions"} | (
            {"choices"} if kind == "choice" else {"scale"} if kind == "score" else set()
        )
        if (
            kind not in ("choice", "score", "boolean")
            or set(q) != fields
            or not isinstance(q.get("instructions"), str)
            or not q["instructions"].strip()
        ):
            raise ValueError("invalid Jev question")
        if kind == "choice":
            choices = q["choices"]
            if (
                not isinstance(choices, dict)
                or not _MIN_OPTIONS <= len(choices) <= _MAX_CHOICES
                or any(
                    not isinstance(k, str)
                    or not k.strip()
                    or not isinstance(v, str)
                    or not v.strip()
                    for k, v in choices.items()
                )
            ):
                raise ValueError("choice requires 2..255 named choices")
        if kind == "score":
            if (
                not isinstance(q["scale"], (list, tuple))
                or not _MIN_OPTIONS <= len(q["scale"]) <= _MAX_SCORE_LABELS
                or any(not isinstance(v, str) or not v.strip() for v in q["scale"])
            ):
                raise ValueError("score requires 2..10 labels")
            q["scale"] = list(q["scale"])
        result[name] = q
    return result


class JevAgent(Agent):
    """A Jev agent with the standard agent execution lifecycle.

    Pass state as the runtime prompt (strings or JSON-serializable mappings).
    With no fixed questions, supply ``context={"questions": ...}`` when starting.
    Credentials and inference stay on Conductor; no local tool workers are needed.
    """

    kind = "jev"

    def __init__(
        self,
        name: str,
        *,
        model: str,
        questions: Optional[Mapping[str, Any]] = None,
        timeout_seconds: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        masked_fields: Optional[list[str]] = None,
    ):
        if not isinstance(model, str) or not model.strip():
            raise ValueError("Jev model must be nonempty")
        super().__init__(
            name=name,
            model=model,
            timeout_seconds=timeout_seconds,
            metadata=metadata,
            masked_fields=masked_fields,
        )
        self.questions = jev_questions(questions) if questions is not None else None


@dataclass(frozen=True)
class JevAnswer:
    type: str
    choice: Optional[str] = None
    score: Optional[float] = None
    probability: Optional[float] = None
    confidence: Optional[float] = None


@dataclass(frozen=True)
class JevResult:
    model: str
    answers: Dict[str, JevAnswer]
    usage: Optional[Dict[str, Any]] = None
    latency_ms: Optional[int] = None
    request_id: Optional[str] = None

    @classmethod
    def from_dict(cls, value: dict) -> "JevResult":
        return cls(
            model=value["model"],
            answers={k: JevAnswer(**v) for k, v in value["answers"].items()},
            usage=value.get("usage"),
            latency_ms=value.get("latencyMs"),
            request_id=value.get("requestId"),
        )
