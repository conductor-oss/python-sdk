"""
For detailed explanation https://github.com/conductor-sdk/conductor-python/blob/main/README.md#step-1-create-a-workflow
"""

from greetings_worker import greet

from conductor.asyncio_client.workflow.conductor_workflow import AsyncConductorWorkflow
from conductor.asyncio_client.workflow.executor.workflow_executor import (
    AsyncWorkflowExecutor,
)


def greetings_workflow(
    workflow_executor: AsyncWorkflowExecutor,
) -> AsyncConductorWorkflow:
    name = "greetings"
    workflow = AsyncConductorWorkflow(name=name, executor=workflow_executor)
    workflow.version = 1
    workflow >> greet(task_ref_name="greet_ref", name=workflow.input("name"))
    return workflow
