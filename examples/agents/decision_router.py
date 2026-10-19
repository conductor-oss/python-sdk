"""Route to one of two chat agents with a decision tool.

When a decision ToolDef is supplied as ``router=``, deployment compiles it into
one decision-backed SWITCH. It is a selector configuration, not a standalone
agent, and needs no Python worker. Pass --run for inference.
"""

import argparse
import json
import os

from conductor.ai.agents import Agent, AgentRuntime, Strategy, ToolDef
from conductor.client.configuration.configuration import Configuration

PROMPT = "The customer reports a duplicate charge on the latest invoice."
CHAT_MODEL = os.getenv("CONDUCTOR_AGENT_LLM_MODEL", "openai/gpt-4o-mini")


def support_router():
    billing = Agent(
        name="billing",
        model=CHAT_MODEL,
        instructions="Help the customer with billing and invoice questions.",
    )
    technical = Agent(
        name="technical",
        model=CHAT_MODEL,
        instructions="Help the customer troubleshoot product issues.",
    )
    selector = ToolDef(
        name="support_selector",
        description="Choose the support agent that should handle the request.",
        tool_type="decision",
        config={
            "model": "jev-1.13",
            **(
                {"provider": os.environ["CONDUCTOR_DECISION_PROVIDER"]}
                if "CONDUCTOR_DECISION_PROVIDER" in os.environ
                else {}
            ),
            "questions": {
                "agent": {
                    "type": "choice",
                    "instructions": "Choose the right support team.",
                    "choices": {
                        "billing": "Payments and invoices",
                        "technical": "Product errors and troubleshooting",
                    },
                }
            },
        },
    )
    return Agent(
        name="decision_support_router",
        strategy=Strategy.ROUTER,
        router=selector,
        agents=[billing, technical],
        max_turns=1,
        synthesize=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    config = Configuration(
        server_api_url=os.environ.get("CONDUCTOR_SERVER_URL", "http://localhost:8080/api")
    )
    with AgentRuntime(config) as runtime:
        agent = support_router()
        if not args.run:
            print(json.dumps(runtime.plan(agent), indent=2))
            return

        runtime.deploy(agent)
        handle = runtime.start(agent, PROMPT)
        print("Execution:", handle.execution_id)
        result = handle.join(timeout=120)
        if not result.is_success:
            raise RuntimeError(f"{result.status}: {result.error}")
        print(json.dumps(result.output, indent=2))


if __name__ == "__main__":
    main()
