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
TASK_NAME = 'async_metadata_probe_task'


def test_async_method(api_client: ApiClient):
    metadata_client = MetadataResourceApi(api_client)

    # Ensure the task def exists so the async lookup has something to return,
    # regardless of test ordering. A bare TaskDef is fine: nothing executes this
    # task, it only needs to be retrievable.
    metadata_client.register_task_def(body=[TaskDef(name=TASK_NAME)])

    try:
        thread = metadata_client.get_task_def(
            async_req=True, tasktype=TASK_NAME)
        thread.wait()
        assert thread.get() is not None
    finally:
        # Don't leave this def behind on a long-lived shared server: the name is
        # fixed rather than run-suffixed, so it isn't matched by
        # leaked_task_defs.TEST_PREFIXES and the reclaim pass would never
        # collect it. cleanup_metadata swallows its own failures, so this can
        # never turn a passing test red.
        from tests.integration.conftest import cleanup_metadata
        cleanup_metadata(api_client.configuration, task_defs=(TASK_NAME,))
