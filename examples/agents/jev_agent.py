"""Compile a Jev agent. Pass --run for inference. Configure credentials on Conductor."""

import argparse
import json
import os

from conductor.ai.agents import AgentRuntime, JevAgent
from conductor.client.configuration.configuration import Configuration

PROMPT = "The customer reports a duplicate charge on the latest invoice."


def support_agent():
    return JevAgent(
        name="jev_support_agent",
        model="jev-1.13",
        questions={
            "department": {
                "type": "choice",
                "instructions": "Which team should handle this issue?",
                "choices": {
                    "billing": "Payment and invoice issues",
                    "technical": "Bugs and software issues",
                    "other": "Other requests",
                },
            }
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Start live Jev inference")
    args = parser.parse_args()
    config = Configuration(
        server_api_url=os.environ.get("CONDUCTOR_SERVER_URL", "http://localhost:8080/api")
    )
    with AgentRuntime(config) as runtime:
        agent = support_agent()
        if not args.run:
            print(json.dumps(runtime.plan(agent, PROMPT), indent=2))
            return

        handle = runtime.start(agent, PROMPT)
        print("Execution:", handle.execution_id)
        result = handle.join(timeout=120)
        if not result.is_success:
            raise RuntimeError(f"{result.status}: {result.error}")
        print(json.dumps(result.output["result"], indent=2))


if __name__ == "__main__":
    main()
