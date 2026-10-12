"""Route a request with one decision-backed SWITCH and an inline branch.

The server evaluates the SWITCH synchronously and selects its branch. Provider
failures fail the workflow without task retries. No Python worker is needed.
Run: CONDUCTOR_SERVER_URL=http://localhost:8080/api python -m examples.agentic_workflows.ai_decision_routing
"""

import argparse
import json
import time

from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.inline import InlineTask
from conductor.client.workflow.task.switch_task import EvaluatorType, SwitchTask


def create_workflow(executor, model="jev-1.13", provider=None) -> ConductorWorkflow:
    workflow = ConductorWorkflow(executor=executor, name="ai_decision_routing", version=1)
    decision = SwitchTask(
        task_ref_name="route_request",
        case_expression="route",
    )
    decision.evaluator_type = EvaluatorType.DECISION.value
    decision.input_parameters = {
        "model": model,
        **({"provider": provider} if provider is not None else {}),
        "state": workflow.input("request"),
        "questions": {
            "route": {
                "type": "choice",
                "instructions": "Choose the team best suited to handle this request.",
                "choices": {
                    "billing": "Payments, invoices, refunds, or subscriptions.",
                    "technical": "Errors, outages, or product troubleshooting.",
                },
            }
        },
    }
    billing = InlineTask(
        "handle_billing",
        script='({team: "billing", nextAction: "review_invoice", '
        'message: "Check invoice line items and payment records.", request: $.request})',
        bindings={"request": workflow.input("request")},
    )
    technical = InlineTask(
        "handle_technical",
        script='({team: "technical", nextAction: "collect_diagnostics", '
        'message: "Collect error logs and steps to reproduce.", request: $.request})',
        bindings={"request": workflow.input("request")},
    )
    decision.switch_case("billing", [billing])
    decision.switch_case("technical", [technical])
    result = InlineTask(
        "selected_result",
        script="$.billing || $.technical",
        bindings={
            "billing": billing.output("result"),
            "technical": technical.output("result"),
        },
    )
    workflow >> decision >> result
    workflow.output_parameters(
        {
            "selectedCase": decision.output("selectedCase"),
            "answers": decision.output("answers"),
            "usage": decision.output("usage"),
            "cost": decision.output("usage.cost"),
            "latencyMs": decision.output("latencyMs"),
            "result": result.output("result"),
        }
    )
    return workflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", default="I was charged twice on my latest invoice.")
    parser.add_argument("--model", default="jev-1.13")
    parser.add_argument("--provider")
    args = parser.parse_args()
    clients = OrkesClients(configuration=Configuration())
    workflow = create_workflow(clients.get_workflow_executor(), args.model, args.provider)
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
