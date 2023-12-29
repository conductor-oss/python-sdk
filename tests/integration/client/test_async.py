from conductor.client.http.api.metadata_resource_api import MetadataResourceApi
from conductor.client.http.api_client import ApiClient


def test_async_method(api_client: ApiClient):
    metadata_client = MetadataResourceApi(api_client)
    thread = metadata_client.get_task_def(
        async_req=True, tasktype='python_integration_test_task')
    thread.wait()
    assert thread.get() is not None
