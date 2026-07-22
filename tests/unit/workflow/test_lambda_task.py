from conductor.client.workflow.task.lambda_task import LambdaTask
from conductor.client.workflow.task.task_type import TaskType

SCRIPT = "(function(){ return {out: $.x + 1}; })()"


def test_lambda_task_builds_script_expression():
    task = LambdaTask(task_ref_name="lambda_ref", script=SCRIPT)
    assert task.task_reference_name == "lambda_ref"
    assert task.input_parameters == {"scriptExpression": SCRIPT}

    workflow_task = task.to_workflow_task()
    assert workflow_task.type == TaskType.LAMBDA.value
    assert workflow_task.input_parameters["scriptExpression"] == SCRIPT


def test_lambda_task_merges_bindings():
    task = LambdaTask(
        task_ref_name="lambda_ref",
        script=SCRIPT,
        bindings={"x": "${workflow.input.x}"},
    )
    assert task.input_parameters == {
        "scriptExpression": SCRIPT,
        "x": "${workflow.input.x}",
    }
