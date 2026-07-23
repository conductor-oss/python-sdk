# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Basic OpenAI Agent — simplest possible agent with no tools.

Demonstrates:
    - Defining an agent using the OpenAI Agents SDK
    - Running it on the Conductor agent runtime (auto-detected)
    - The runtime serializes the agent generically and the server
      normalizes the OpenAI-specific config into a Conductor workflow.

Requirements:
    - pip install openai-agents
    - Conductor server with OpenAI LLM integration configured
    - CONDUCTOR_SERVER_URL=http://localhost:8080/api as environment variable
    - CONDUCTOR_AGENT_LLM_MODEL=openai/gpt-4o-mini as environment variable
"""

from agents import Agent

from conductor.ai.agents import AgentRuntime

from settings import settings

agent = Agent(
    name="greeter",
    instructions="You are a friendly assistant. Keep your responses concise and helpful.",
    model=settings.llm_model,
)


if __name__ == "__main__":
    with AgentRuntime() as runtime:
        result = runtime.run(agent, "Say hello and tell me a fun fact about the Python programming language.")
        result.print_result()

        # Production pattern:
        # 1. Deploy once during CI/CD:
        # runtime.deploy(agent)
        # CLI alternative:
        # runtime.deploy(agent) from a release script
        #
        # 2. In a separate long-lived worker process:
        # runtime.serve(agent)
