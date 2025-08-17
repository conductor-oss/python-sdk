"""
This file contains a Simple Worker that can be used in any workflow.
For detailed information https://github.com/conductor-sdk/conductor-python/blob/main/README.md#step-2-write-worker
"""

from conductor.asyncio_client.worker.worker_task import worker_task


@worker_task(task_definition_name="greet")
def greet(name: str) -> str:
    return f"Hello {name}"
