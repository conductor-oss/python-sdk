#!/usr/bin/env python3
"""Basic agent — the simplest possible Conductor example."""

from conductor.ai.agents import Agent, AgentRuntime

agent = Agent(
    name="greeter",
    model="anthropic/claude-sonnet-4-6",
    instructions="You are a friendly assistant. Keep responses brief.",
)

prompt = "Hello! What can you do?"

if __name__ == "__main__":
    with AgentRuntime() as rt:
        result = rt.run(agent, prompt)
        result.print_result()

        # Production pattern:
        # 1. Deploy once during CI/CD:
        # rt.deploy(agent)
        # CLI alternative:
        # runtime.deploy(agent) from a release script
        #
        # 2. In a separate long-lived worker process:
        # rt.serve(agent)
