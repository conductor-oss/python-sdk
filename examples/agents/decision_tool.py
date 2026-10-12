"""Use Decision inference as a tool inside a normal chat agent.

The server executes the tool as a branchless decision-backed SWITCH, so no Python
worker is needed.
"""

import os

from conductor.ai.agents import Agent, AgentRuntime, ToolDef
from conductor.client.configuration.configuration import Configuration

decision_config = {
    "model": "jev-1.13",
    **(
        {"provider": os.environ["CONDUCTOR_DECISION_PROVIDER"]}
        if "CONDUCTOR_DECISION_PROVIDER" in os.environ
        else {}
    ),
    "questions": {
        "department": {
            "type": "choice",
            "instructions": "Choose the correct support department.",
            "choices": {
                "billing": "Payments and invoices",
                "technical": "Product errors and troubleshooting",
            },
        }
    },
}

classify_request = ToolDef(
    name="classify_request",
    description="Classify the customer request before answering.",
    tool_type="decision",
    input_schema={
        "type": "object",
        "properties": {"state": {"type": "string"}},
        "required": ["state"],
    },
    config=decision_config,
)

support_agent = Agent(
    name="decision_tool_support",
    model=os.getenv("CONDUCTOR_AGENT_LLM_MODEL", "openai/gpt-4o-mini"),
    instructions="Call classify_request before answering the customer.",
    tools=[classify_request],
)


def main():
    config = Configuration(
        server_api_url=os.getenv("CONDUCTOR_SERVER_URL", "http://localhost:8080/api")
    )
    with AgentRuntime(config) as runtime:
        result = runtime.run(
            support_agent,
            "I was charged twice on my latest invoice.",
        )
        if not result.is_success:
            raise RuntimeError(result.error)
        print(result.output)


if __name__ == "__main__":
    main()
