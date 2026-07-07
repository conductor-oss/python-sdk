"""
Module-level helpers for spawn start-method regression tests.

These MUST live in an importable module (not the test file's local scope):
the 'spawn' start method pickles Process arguments by reference, and the
child process re-imports this module to resolve them.

Regression tests for GitHub issues #264 / #271:
@worker_task workers were unpicklable ("cannot pickle '_thread.lock' object" /
"it's not the same object as module.name"), so TaskHandler could not start
worker subprocesses with CONDUCTOR_MP_START_METHOD=spawn (the only safe start
method on macOS).
"""
from conductor.client.http.models.task import Task
from conductor.client.worker.worker_task import worker_task


@worker_task(task_definition_name="spawn_pickle_task", thread_count=2, domain="spawn-test")
def spawn_pickle_task(x: int) -> dict:
    return {"doubled": x * 2}


@worker_task(task_definition_name="spawn_pickle_async_task")
async def spawn_pickle_async_task(x: int) -> dict:
    return {"echo": x}


def plain_function_worker(x: int) -> dict:
    """Module-level function NOT wrapped by @worker_task."""
    return {"plain": x}


def run_worker_in_child(worker, result_queue) -> None:
    """Spawn-child entry point: execute one task on the unpickled worker.

    Receiving `worker` here already exercises unpickling inside the child.
    """
    task = Task(
        task_id="spawn-child-task-id",
        workflow_instance_id="spawn-child-wf-id",
        task_def_name=worker.get_task_definition_name(),
        input_data={"x": 21},
        status="IN_PROGRESS",
    )
    result = worker.execute(task)
    result_queue.put((str(result.status), result.output_data))
