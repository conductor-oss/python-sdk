# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Extended agent types — specialised agent classes for common patterns.

- :class:`GPTAssistantAgent` — wraps the OpenAI Assistants API as an Agent.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from conductor.ai.agents.agent import Agent

logger = logging.getLogger("conductor.ai.agents.ext")


# ── OpenAI Assistants API call ─────────────────────────────────────────


class _AssistantCall:
    """Spawn-safe callable that runs a message against the OpenAI Assistants API.

    A module-level class (not a closure over the Agent) so the registered
    worker pickles by value — every attribute is plain data. This is what makes
    the auto-generated ``*_assistant_call`` tool safe under the ``spawn`` start
    method (a ``<locals>`` closure over ``self`` would not be importable).
    """

    def __init__(
        self,
        assistant_id: Optional[str] = None,
        api_key: Optional[str] = None,
        openai_tools: Optional[List[Dict[str, Any]]] = None,
        model: str = "openai/gpt-4o",
        instructions: str = "",
    ) -> None:
        self.assistant_id = assistant_id
        self.api_key = api_key
        self.openai_tools = list(openai_tools or [])
        self.model = model
        self.instructions = instructions

    def __call__(self, message: str) -> str:
        """Send a message to the OpenAI Assistant and get a response."""
        try:
            import openai
        except ImportError:
            return "Error: openai package not installed. Install with: pip install openai"

        import os

        api_key = self.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return "Error: No OpenAI API key provided."

        client = openai.OpenAI(api_key=api_key)

        # Create assistant if needed
        assistant_id = self.assistant_id
        if not assistant_id:
            model_name = self.model.split("/", 1)[-1]
            assistant = client.beta.assistants.create(
                model=model_name,
                instructions=self.instructions,
                tools=self.openai_tools,
            )
            assistant_id = assistant.id
            self.assistant_id = assistant_id

        try:
            # Create thread and run
            thread = client.beta.threads.create()
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message,
            )

            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant_id,
            )

            if run.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                for msg in messages.data:
                    if msg.role == "assistant":
                        parts = []
                        for block in msg.content:
                            if hasattr(block, "text"):
                                parts.append(block.text.value)
                        if parts:
                            return "\n".join(parts)
                return "No response from assistant."
            else:
                return f"Assistant run ended with status: {run.status}"

        except Exception as e:
            return f"OpenAI Assistant error: {e}"


# ── GPTAssistantAgent ──────────────────────────────────────────────────


class GPTAssistantAgent(Agent):
    """An agent backed by the OpenAI Assistants API.

    Wraps an OpenAI Assistant (with its own instructions, tools, and
    file search capabilities) as a Conductor Agent.  The assistant's
    execution is handled via the Assistants API Threads and Runs.

    Requires the ``openai`` package.

    Args:
        name: Agent name.
        assistant_id: Existing OpenAI Assistant ID. If ``None``, a new
            assistant is created using the provided instructions and model.
        model: OpenAI model (e.g. ``"gpt-4o"``). Only used when creating
            a new assistant.
        instructions: System instructions for the assistant.
        openai_tools: OpenAI-native tools config (e.g.
            ``[{"type": "code_interpreter"}]``).
        api_key: OpenAI API key. If ``None``, uses the ``OPENAI_API_KEY``
            environment variable.

    Example::

        from conductor.ai.agents.ext import GPTAssistantAgent

        # Use an existing assistant
        agent = GPTAssistantAgent(
            name="coder",
            assistant_id="asst_abc123",
        )

        # Or create one on the fly
        agent = GPTAssistantAgent(
            name="analyst",
            model="gpt-4o",
            instructions="You are a data analyst.",
            openai_tools=[{"type": "code_interpreter"}],
        )
    """

    def __init__(
        self,
        name: str,
        assistant_id: Optional[str] = None,
        model: str = "openai/gpt-4o",
        instructions: str = "",
        openai_tools: Optional[List[Dict[str, Any]]] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.assistant_id = assistant_id
        self.openai_tools = openai_tools or []
        self._api_key = api_key

        # Mark via metadata
        metadata = kwargs.pop("metadata", {}) or {}
        metadata["_agent_type"] = "gpt_assistant"
        if assistant_id:
            metadata["_assistant_id"] = assistant_id

        # Normalise the model string
        if "/" not in model:
            model = f"openai/{model}"

        # Build the tool that calls the Assistants API. Backed by a module-level
        # callable (not a closure) so the registered worker is spawn-safe.
        from conductor.ai.agents.tool import tool

        runner = _AssistantCall(
            assistant_id=assistant_id,
            api_key=api_key,
            openai_tools=self.openai_tools,
            model=model,
            instructions=instructions or "You are a helpful assistant.",
        )
        call_assistant = tool(name=f"{name}_assistant_call")(runner)

        tools = kwargs.pop("tools", []) or []
        tools.append(call_assistant)

        super().__init__(
            name=name,
            model=model,
            instructions=instructions or "You are a helpful assistant.",
            tools=tools,
            metadata=metadata,
            max_turns=1,
            **kwargs,
        )

    def _run_assistant(self, message: str) -> str:
        """Execute a message against the OpenAI Assistants API.

        Delegates to :class:`_AssistantCall` (the same logic the worker runs),
        propagating a lazily-created assistant id back onto the agent.
        """
        instructions = self.instructions() if callable(self.instructions) else self.instructions
        runner = _AssistantCall(
            assistant_id=self.assistant_id,
            api_key=self._api_key,
            openai_tools=self.openai_tools,
            model=self.model,
            instructions=instructions,
        )
        result = runner(message)
        self.assistant_id = runner.assistant_id
        return result

    def __repr__(self) -> str:
        return f"GPTAssistantAgent(name={self.name!r}, assistant_id={self.assistant_id!r})"
