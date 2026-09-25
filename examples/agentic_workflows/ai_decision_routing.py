"""Route a request with AI_DECISION → SWITCH → SET_VARIABLE.

Requires server-side AI_DECISION support and Jev credentials. No worker needed.
Run: CONDUCTOR_SERVER_URL=http://localhost:8080/api python -m examples.agentic_workflows.ai_decision_routing
"""

import argparse
import json
import time

from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.ai_decision_task import AiDecisionTask
from conductor.client.workflow.task.set_variable_task import SetVariableTask
from conductor.client.workflow.task.switch_task import SwitchTask


def create_workflow(executor) -> ConductorWorkflow:
    workflow = ConductorWorkflow(executor=executor, name="ai_decision_routing", version=1)
    decision = AiDecisionTask(
        task_ref_name="decision",
        model="jev-1.13",
        state=workflow.input("request"),
        questions={
            "route": {
                "type": "choice",
                "instructions": "Choose the team best suited to handle this request.",
                "choices": {
                    "billing": "Payments, invoices, refunds, or subscriptions.",
                    "technical": "Errors, outages, or product troubleshooting.",
                },
            }
        },
    )
    route = SwitchTask("route_request", decision.output("selectedCase"))
    route.switch_case("billing", [
        SetVariableTask("assign_billing").input_parameter("team", "billing"),
    ])
    route.switch_case("technical", [
        SetVariableTask("assign_technical").input_parameter("team", "technical"),
    ])
    workflow >> decision >> route
    workflow.output_parameters({
        "decision": decision.output(),
        "team": "${workflow.variables.team}",
    })
    return workflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", default="I was charged twice on my latest invoice.")
    args = parser.parse_args()
    clients = OrkesClients(configuration=Configuration())
    workflow = create_workflow(clients.get_workflow_executor())
    workflow.register(overwrite=True)
    workflow_id = workflow.start_workflow_with_input({"request": args.request})
    print(f"Workflow: {workflow_id}")
    client = clients.get_workflow_client()
    while True:
        result = client.get_workflow(workflow_id=workflow_id, include_tasks=False)
        if result.is_completed():
            break
        time.sleep(1)
    if result.status != "COMPLETED":
        raise SystemExit(f"{result.status}: {result.reason_for_incompletion}")
    print(json.dumps(result.output, indent=2))


if __name__ == "__main__":
    main()
