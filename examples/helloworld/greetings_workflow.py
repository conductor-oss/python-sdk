"""
For detailed explanation https://github.com/conductor-sdk/conductor-python/blob/main/README.md#step-1-create-a-workflow
"""
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from helloworld import greetings_worker


def greetings_workflow(workflow_executor: WorkflowExecutor) -> ConductorWorkflow:
    name = 'greetings'
    workflow = ConductorWorkflow(name=name, executor=workflow_executor)
    workflow.version = 1
    workflow >> greet(task_ref_name='greet_ref', name=workflow.input('name'))
    return workflow
