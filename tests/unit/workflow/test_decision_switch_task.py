from conductor.client.http.api_client import ApiClient
from conductor.client.workflow.task.switch_task import SwitchTask
from examples.agentic_workflows.ai_decision_routing import create_workflow


def serialize(value):
    return ApiClient().sanitize_for_serialization(value)


def test_direct_example_serializes_one_decision_backed_switch():
    definition = serialize(create_workflow(None, provider="typesafe").to_workflow_def())
    decision_tasks = [
        task for task in definition["tasks"] if task.get("evaluatorType") == "decision"
    ]

    assert len(decision_tasks) == 1
    decision = decision_tasks[0]
    assert decision["type"] == "SWITCH"
    assert "AI_DECISION" not in str(definition)
    assert decision["expression"] == "route"

    inputs = decision["inputParameters"]
    assert inputs["model"] == "jev-1.13"
    assert inputs["provider"] == "typesafe"
    assert inputs["state"] == "${workflow.input.request}"
    assert set(inputs["questions"]) == {"route"}
    choice_keys = set(inputs["questions"][decision["expression"]]["choices"])
    assert choice_keys == set(decision["decisionCases"])

    assert not {
        "retryCount",
        "retryLogic",
        "retryDelaySeconds",
        "backoffScaleFactor",
        "maxRetryDelaySeconds",
        "asyncComplete",
    }.intersection(decision)

    assert definition["outputParameters"] == {
        "selectedCase": "${route_request.output.selectedCase}",
        "answers": "${route_request.output.answers}",
        "usage": "${route_request.output.usage}",
        "cost": "${route_request.output.usage.cost}",
        "latencyMs": "${route_request.output.latencyMs}",
        "result": "${selected_result.output.result}",
    }


def test_direct_example_omits_unspecified_provider():
    definition = serialize(create_workflow(None).to_workflow_def())
    assert "provider" not in definition["tasks"][0]["inputParameters"]


def test_existing_value_param_switch_serialization_is_unchanged():
    task = SwitchTask("route", "${workflow.input.route}")

    assert serialize(task.to_workflow_task()) == {
        "name": "route",
        "taskReferenceName": "route",
        "inputParameters": {"switchCaseValue": "${workflow.input.route}"},
        "type": "SWITCH",
        "decisionCases": {},
        "defaultCase": [],
        "evaluatorType": "value-param",
        "expression": "switchCaseValue",
    }


def test_existing_javascript_switch_serialization_is_unchanged():
    task = SwitchTask("route", "return $.route;", use_javascript=True)

    assert serialize(task.to_workflow_task()) == {
        "name": "route",
        "taskReferenceName": "route",
        "inputParameters": {},
        "type": "SWITCH",
        "decisionCases": {},
        "defaultCase": [],
        "evaluatorType": "graaljs",
        "expression": "return $.route;",
    }
