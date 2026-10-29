from __future__ import annotations

import json
import os
from typing import Any, Optional

from conductor.ai.agents import Agent, agent_tool

from agentic.story_concepts import StoryConcept

# Names stay fixed across concepts: worker task names derive from the agent name
# (e.g. python_storyteller_stop_when), so a stable name means the worker processes
# forked at startup keep serving every later concept and no fork happens mid-run.
# The python_ prefix lets other SDK harnesses share a cluster without collisions.
STORYTELLER_NAME = "python_storyteller"
CRITIC_NAME = "python_story_critic"
CRITIC_TOOL_NAME = "story_critic"

_VERDICT_SHAPE = '{"done": true or false, "missing": ["short instruction", ...], "note": "one sentence"}'
_MAX_SEARCH_DEPTH = 6


def build_storyteller(concept: StoryConcept, model: str, max_turns: int) -> Agent:
    critic = Agent(
        name=CRITIC_NAME,
        model=model,
        instructions=_critic_instructions(concept),
        max_tokens=512,
    )
    return Agent(
        name=STORYTELLER_NAME,
        model=model,
        instructions=_storyteller_instructions(concept),
        tools=[
            agent_tool(
                critic,
                name=CRITIC_TOOL_NAME,
                description=(
                    "Judge whether the story meets every requirement. Pass the COMPLETE "
                    "story so far: every sentence, in order."
                ),
            )
        ],
        stop_when=story_is_complete,
        max_turns=max_turns,
        max_tokens=2048,
    )


def story_prompt(setting: str) -> str:
    """The user prompt for one run. Shared so every caller sends identical bytes,
    which replaying recordings through mock/mockLLM depends on."""
    # Settings like "... at 3 a.m." already end in a period.
    return f"Write the story. It is set in {setting.rstrip('.')}."


def _storyteller_instructions(concept: StoryConcept) -> str:
    return (
        "You are writing a short story one sentence at a time, starting from a blank page.\n\n"
        "The finished story must satisfy every one of these requirements:\n"
        f"{concept.rubric()}\n\n"
        "Each turn:\n"
        "1. Write exactly ONE new sentence that continues the story.\n"
        f"2. Call {CRITIC_TOOL_NAME} with the COMPLETE story so far: every sentence, in order, "
        "including the one you just wrote.\n"
        "3. Read the critic's verdict and use its list of missing elements to choose your "
        "next sentence.\n\n"
        "Never rewrite or remove an earlier sentence. Keep each sentence under 30 words.\n"
        f"When the critic says the story is done, do not call {CRITIC_TOOL_NAME} again: "
        "reply with the complete final story as plain text."
    )


def _critic_instructions(concept: StoryConcept) -> str:
    return (
        "You are a strict but fair story editor. You will receive a story draft.\n\n"
        "Decide whether the draft satisfies EVERY requirement below and reads as a complete "
        "story with a beginning, a middle and an end:\n"
        f"{concept.rubric()}\n\n"
        "Respond with ONLY a JSON object and no other text, in exactly this shape:\n"
        f"{_VERDICT_SHAPE}\n\n"
        'Set "done" to true only if every requirement is clearly met. Otherwise list each '
        'unmet requirement in "missing" as a short instruction for the next sentence, for '
        'example "introduce the conflict" or "resolve it through a small act of courage".'
    )


def story_is_complete(context: dict) -> bool:
    """Loop exit gate: True once the critic's latest verdict says the story is done.

    Runs as a worker in a spawned process, so it must stay a module-level function:
    spawn pickling cannot carry closures. ``context["messages"]`` is the LLM's *input*
    history, so the newest verdict it can see is the previous turn's -- the loop ends
    at most one turn after the critic approves.
    """
    iteration = context.get("iteration", 0)
    verdict = find_verdict(context.get("messages"))
    if verdict is None:
        if _is_debug_enabled():
            print(f"[{STORYTELLER_NAME}] turn {iteration}: no verdict yet; "
                  f"messages={_truncate(context.get('messages'))}")
        return False
    done = verdict.get("done") is True
    print(f"[{STORYTELLER_NAME}] turn {iteration}: latest verdict done={done} "
          f"missing={verdict.get('missing')}")
    return done


def find_verdict(node: Any, depth: int = 0) -> Optional[dict]:
    """Return the newest dict carrying a boolean ``done``, searching newest-first.

    The exact shape of a tool result inside the message history is not part of any
    published contract, so search the structure rather than index into it.
    """
    if depth > _MAX_SEARCH_DEPTH:
        return None
    if isinstance(node, str):
        node = _parse_json_object(node)
    if isinstance(node, dict):
        if isinstance(node.get("done"), bool):
            return node
        for value in node.values():
            found = find_verdict(value, depth + 1)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in reversed(node):
            found = find_verdict(item, depth + 1)
            if found is not None:
                return found
    return None


def _parse_json_object(text: str) -> Optional[dict]:
    """Parse a JSON object from model output, tolerating code fences and stray prose."""
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(text[start:end + 1])
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _is_debug_enabled() -> bool:
    return os.environ.get("HARNESS_AGENTIC_DEBUG", "").strip().lower() in ("1", "true", "yes", "on")


def _truncate(value: Any, limit: int = 2000) -> str:
    text = repr(value)
    return text if len(text) <= limit else text[:limit] + "...(truncated)"
