from conductor.client.http.api.metadata_resource_api import MetadataResourceApi
from conductor.client.http.api_client import ApiClient
from conductor.client.http.models.task_def import TaskDef

TASK_NAME = 'python_integration_test_task'


def test_async_method(api_client: ApiClient):
    metadata_client = MetadataResourceApi(api_client)

    # Ensure the task def exists so the async lookup has something to return,
    # regardless of test ordering.
    metadata_client.register_task_def(body=[TaskDef(name=TASK_NAME)])

    thread = metadata_client.get_task_def(
        async_req=True, tasktype=TASK_NAME)
    thread.wait()
    assert thread.get() is not None
