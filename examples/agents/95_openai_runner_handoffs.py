# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""OpenAI Agents SDK migration — multi-agent handoffs.

This is examples/agent_patterns/routing.py from the openai-agents SDK
with exactly ONE line changed.

Before (runs directly against OpenAI):
    from agents import Runner

After (runs on Conductor — durable, observable, scalable):
    from conductor.ai import Runner

The diff:
    -from agents import Runner
    +from conductor.ai import Runner

Agent definitions, handoffs list, and the Runner.run() call are unchanged.
Conductor records every handoff decision in the execution history — you can
replay the full agent-to-agent routing in the Conductor UI.

Requirements:
    - uv add openai-agents
    - CONDUCTOR_SERVER_URL=http://localhost:8080/api
    - CONDUCTOR_AGENT_LLM_MODEL=openai/gpt-4o

Usage:
    python 95_openai_runner_handoffs.py
"""

import asyncio

from agents import Agent

# ── Only this line changes ──────────────────────────────────────────────────
# from agents import Runner          # ← original (runs directly on OpenAI)
from conductor.ai import Runner         # ← Conductor (runs on Conductor)
# ───────────────────────────────────────────────────────────────────────────

french_agent = Agent(
    name="french_agent",
    instructions="You only speak French.",
)

spanish_agent = Agent(
    name="spanish_agent",
    instructions="You only speak Spanish.",
)

english_agent = Agent(
    name="english_agent",
    instructions="You only speak English.",
)

triage_agent = Agent(
    name="triage_agent",
    instructions="Handoff to the appropriate agent based on the language of the request.",
    handoffs=[french_agent, spanish_agent, english_agent],
)


async def main():
    result = await Runner.run(
        triage_agent,
        input="Hello, how do I say good evening in French?",
    )
    print(result.final_output)
    # Bonsoir !


if __name__ == "__main__":
    asyncio.run(main())
