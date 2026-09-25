"""Luna-6 selects one of ten Jev specialists using server-side routing.

Pass --model INTEGRATION/luna-6. Compile by default, --run for inference.
"""

import argparse
import json
import os

from conductor.ai.agents import Agent, AgentRuntime, Strategy
from conductor.client.configuration.configuration import Configuration
from jev_specialists import SPECIALTIES, specialists


def triage_agent(model):
    candidates = specialists()
    descriptions = "\n".join(
        f"{agent.name}: {SPECIALTIES[name][1]}" for name, agent in candidates.items()
    )
    return Agent(
        name="luna_jev_triage",
        model=model,
        strategy=Strategy.ROUTER,
        router=Agent(
            name="luna_jev_selector",
            model=model,
            instructions=f"Select exactly one specialist for the request. Return only its agent name.\n{descriptions}",
        ),
        agents=list(candidates.values()),
        max_turns=1,
        synthesize=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.getenv("CONDUCTOR_AGENT_LLM_MODEL"))
    parser.add_argument("--run", action="store_true")
    parser.add_argument(
        "--prompt", default="Our webhook endpoint returns 503 and order notifications are missing."
    )
    args = parser.parse_args()
    if not args.model:
        parser.error("Pass --model with your server's integration/luna-6 identifier")
    config = Configuration(
        server_api_url=os.getenv("CONDUCTOR_SERVER_URL", "http://localhost:8080/api")
    )
    with AgentRuntime(config) as runtime:
        agent = triage_agent(args.model)
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
