"""Three levels: Jev department selector, Jev specialist selector, Jev specialist.

Requires server support for Jev routers. Compile by default, --run for inference.
"""

import argparse
import json
import os

from conductor.ai.agents import Agent, AgentRuntime, JevAgent, Strategy
from conductor.client.configuration.configuration import Configuration
from jev_specialists import SPECIALTIES, specialists

PROMPT = "Our latest invoice has two settled charges with different transaction IDs for the same purchase."


def routing_team(name, children, descriptions):
    return Agent(
        name=name,
        strategy=Strategy.ROUTER,
        router=JevAgent(
            name=f"{name}_selector",
            model="jev-1.13",
            questions={
                "agent": {
                    "type": "choice",
                    "instructions": "Choose the agent best suited to handle this request.",
                    "choices": descriptions,
                }
            },
        ),
        agents=children,
        max_turns=1,
        synthesize=False,
    )


def triage_agent():
    leaves = specialists()
    departments = []
    for department in ("billing", "technical", "account"):
        members = {
            name: agent for name, agent in leaves.items() if SPECIALTIES[name][0] == department
        }
        departments.append(
            routing_team(
                f"jev_{department}_team",
                list(members.values()),
                {agent.name: SPECIALTIES[name][1] for name, agent in members.items()},
            )
        )
    return routing_team(
        "jev_nested_triage",
        departments,
        {
            "jev_billing_team": "Charges, refunds and subscriptions",
            "jev_technical_team": "API errors, outages, integrations and setup",
            "jev_account_team": "Access, security and privacy",
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--prompt", default=PROMPT)
    args = parser.parse_args()
    config = Configuration(
        server_api_url=os.getenv("CONDUCTOR_SERVER_URL", "http://localhost:8080/api")
    )
    with AgentRuntime(config) as runtime:
        agent = triage_agent()
        if not args.run:
            print(json.dumps(runtime.plan(agent, args.prompt), indent=2))
            return
        runtime.deploy(agent)
        handle = runtime.start(agent, args.prompt)
        print("Execution:", handle.execution_id)
        result = handle.join(timeout=180)
        if not result.is_success:
            raise RuntimeError(result.error)
        print(json.dumps(result.output, indent=2))


if __name__ == "__main__":
    main()
