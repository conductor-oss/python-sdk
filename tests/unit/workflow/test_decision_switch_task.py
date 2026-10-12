import pytest

from conductor.client.http.api_client import ApiClient
from conductor.client.workflow.task.switch_task import SwitchTask
from examples.agentic_workflows.ai_decision_routing import create_workflow


def test_direct_example_serializes_decision_switch_and_branches():
    definition = ApiClient().sanitize_for_serialization(
        create_workflow(None, provider="typesafe").to_workflow_def()
    )
    decision = definition["tasks"][0]
    inputs = decision["inputParameters"]
    assert (decision["type"], decision["evaluatorType"], decision["expression"]) == (
        "SWITCH",
        "decision",
        "route",
    )
    assert inputs["model"] == "jev-1.13"
    assert inputs["provider"] == "typesafe"
    assert inputs["state"] == "${workflow.input.request}"
    assert set(inputs["questions"]["route"]["choices"]) == set(decision["decisionCases"])
    assert not {"retryCount", "asyncComplete"}.intersection(decision)
    assert definition["outputParameters"]["selectedCase"] == "${route_request.output.selectedCase}"
    assert definition["outputParameters"]["result"] == "${selected_result.output.result}"


@pytest.mark.parametrize(
    ("javascript", "expression", "inputs", "evaluator", "serialized_expression"),
    [
        (
            False,
            "${workflow.input.route}",
            {"switchCaseValue": "${workflow.input.route}"},
            "value-param",
            "switchCaseValue",
        ),
        (True, "return $.route;", {}, "graaljs", "return $.route;"),
    ],
)
def test_existing_switch_serialization(
    javascript, expression, inputs, evaluator, serialized_expression
):
    task = SwitchTask("route", expression, use_javascript=javascript)
    assert ApiClient().sanitize_for_serialization(task.to_workflow_task()) == {
        "name": "route",
        "taskReferenceName": "route",
        "inputParameters": inputs,
        "type": "SWITCH",
        "decisionCases": {},
        "defaultCase": [],
        "evaluatorType": evaluator,
        "expression": serialized_expression,
    }
