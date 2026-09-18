from conductor.client.http.api.metadata_resource_api import MetadataResourceApi
from conductor.client.http.api_client import ApiClient
from conductor.client.http.models.task_def import TaskDef

# Owned by this test alone. It used to reuse 'python_integration_test_task',
# which tests/integration/workflow/test_workflow_execution.py registers with
# real timeouts and actually runs workflows against -- and since this file and
# that one run as separate concurrent CI jobs against the same server, whichever
# registered last won. This file only needs *some* task def to exist for the
# async lookup below, so it registers its own instead of overwriting one another
# suite depends on.
#
# Fixed name on purpose, and no teardown: POST /metadata/taskdefs upserts and
# this def's content never varies, so it costs exactly one task-def slot however
# many times the suite runs. A per-run name (as in leaked_task_defs.TEST_PREFIXES)
# would register a new def every run -- the leak that reached the 402 cap -- and
# deleting a shared fixed name is worse still: it can race a concurrent run
# between its register and its lookup.
TASK_NAME = 'async_metadata_probe_task'


def test_async_method(api_client: ApiClient):
    metadata_client = MetadataResourceApi(api_client)

    # Ensure the task def exists so the async lookup has something to return,
    # regardless of test ordering. A bare TaskDef is fine: nothing executes this
    # task, it only needs to be retrievable.
    metadata_client.register_task_def(body=[TaskDef(name=TASK_NAME)])

    thread = metadata_client.get_task_def(
        async_req=True, tasktype=TASK_NAME)
    thread.wait()
    assert thread.get() is not None
