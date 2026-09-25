from conductor.client.http.api_client import ApiClient
from conductor.client.workflow.task.ai_decision_task import AiDecisionTask
from conductor.client.workflow.task.task_type import TaskType
from examples.agentic_workflows.ai_decision_routing import create_workflow


def test_ai_decision_references_and_serialization():
    questions = {
        "route": {
            "type": "choice",
            "instructions": "Choose a team.",
            "choices": {"billing": "Payments", "technical": "Errors"},
        }
    }
    task = AiDecisionTask("decision", "jev-1.13", "${workflow.input.request}", questions)
    serialized = ApiClient().sanitize_for_serialization(task.to_workflow_task())
    assert task.task_type == TaskType.AI_DECISION
    assert serialized["type"] == "AI_DECISION"
    assert serialized["name"] == "ai_decision"
    assert serialized["taskReferenceName"] == "decision"
    assert serialized["inputParameters"] == {
        "model": "jev-1.13",
        "state": "${workflow.input.request}",
        "questions": questions,
    }
    assert task.input("state") == "${decision.input.state}"
    assert task.output() == "${decision.output}"
    assert task.output("answers.route.choice") == "${decision.output.answers.route.choice}"
    assert task.output("selectedCase") == "${decision.output.selectedCase}"


def test_custom_name_and_input_reference():
    task = AiDecisionTask("decision", "jev-1.13", "request", {}, task_name="choose_team")
    task.input_parameter("questions", "${workflow.input.questions}")
    definition = task.to_workflow_task()
    assert definition.name == "choose_team"
    assert definition.input_parameters["questions"] == "${workflow.input.questions}"


def test_routing_example_preserves_decision_output():
    definition = ApiClient().sanitize_for_serialization(create_workflow(None).to_workflow_def())
    decision, switch, result = definition["tasks"]
    assert decision["type"] == "AI_DECISION"
    assert decision["inputParameters"]["state"] == "${workflow.input.request}"
    assert switch["type"] == "SWITCH"
    assert switch["evaluatorType"] == "value-param"
    assert switch["inputParameters"]["switchCaseValue"] == "${decision.output.selectedCase}"
    assert set(switch["decisionCases"]) == {"billing", "technical"}
    for team, tasks in switch["decisionCases"].items():
        assert len(tasks) == 1
        assert tasks[0]["type"] == "INLINE"
        assert tasks[0]["taskReferenceName"] == f"handle_{team}"
        assert tasks[0]["inputParameters"]["request"] == "${workflow.input.request}"
    assert result["type"] == "INLINE"
    assert result["inputParameters"]["billing"] == "${handle_billing.output.result}"
    assert result["inputParameters"]["technical"] == "${handle_technical.output.result}"
    assert definition["outputParameters"] == {
        "decision": "${decision.output}",
        "result": "${selected_result.output.result}",
    }
