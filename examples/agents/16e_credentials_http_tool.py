# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Credentials — HTTP tool with server-side credential resolution.

Demonstrates:
    - http_tool() with credentials=["GITHUB_TOKEN"]
    - ${GITHUB_TOKEN} in headers resolved server-side (not in Python)
    - No worker process needed — Conductor makes the HTTP call directly

The ${NAME} syntax in headers tells the server to substitute the credential
value from the store at execution time. The plaintext value never appears
in the workflow definition.

Setup (one-time):
    the Conductor server credential store
Requirements:
    - Conductor server running at CONDUCTOR_SERVER_URL
    - CONDUCTOR_AGENT_LLM_MODEL set (or defaults to openai/gpt-5.4)
    - GITHUB_TOKEN stored via `the Conductor server credential store`
"""

from conductor.ai.agents import Agent, AgentRuntime
from conductor.ai.agents.tool import http_tool
from settings import settings


# HTTP tool with credential-bearing headers.
# ${GITHUB_TOKEN} is resolved server-side from the credential store.
list_repos = http_tool(
    name="list_github_repos",
    description="List public GitHub repositories for a user. Returns JSON array with name, url, and stars.",
    url="https://api.github.com/users/Conductor/repos?per_page=5&sort=updated",
    headers={
        "Authorization": "Bearer ${GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    },
    credentials=["GITHUB_TOKEN"],
)

agent = Agent(
    name="github_http_agent",
    model=settings.llm_model,
    tools=[list_repos],
    instructions="You list GitHub repos using the list_github_repos tool. Summarize the results.",
)


if __name__ == "__main__":
    with AgentRuntime() as runtime:
        result = runtime.run(agent, "List the repos for Conductor")
        result.print_result()

        # Production pattern:
        # 1. Deploy once during CI/CD:
        # runtime.deploy(agent)
        # CLI alternative:
        # runtime.deploy(agent) from a release script
        #
        # 2. In a separate long-lived worker process:
        # runtime.serve(agent)

