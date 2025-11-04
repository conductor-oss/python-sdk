import json
import logging

import pytest

from conductor.asyncio_client.adapters.api.metadata_resource_api import (
    MetadataResourceApiAdapter,
)
from conductor.asyncio_client.adapters.api.tags_api import TagsApiAdapter
from conductor.asyncio_client.adapters.models.extended_task_def_adapter import (
    ExtendedTaskDefAdapter,
)
from conductor.asyncio_client.adapters.models.extended_workflow_def_adapter import (
    ExtendedWorkflowDefAdapter,
)
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.adapters.models.task_def_adapter import TaskDefAdapter
from conductor.asyncio_client.adapters.models.workflow_def_adapter import (
    WorkflowDefAdapter,
)
from conductor.asyncio_client.adapters.models.workflow_task_adapter import (
    WorkflowTaskAdapter,
)
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.rest import ApiException
from conductor.asyncio_client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.asyncio_client.adapters import ApiClient

WORKFLOW_NAME = "ut_wf"
WORKFLOW_TASK_REF = "ut_wf_ref"
TASK_NAME = "ut_task"


@pytest.fixture(scope="module")
def metadata_client():
    configuration = Configuration("http://localhost:8080/api")
    api_client = ApiClient(configuration)
    return OrkesMetadataClient(configuration, api_client=api_client)


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def workflow_def():
    return WorkflowDefAdapter(
        name=WORKFLOW_NAME,
        version=1,
        timeout_seconds=1,
        tasks=[
            WorkflowTaskAdapter(name=TASK_NAME, task_reference_name=WORKFLOW_TASK_REF)
        ],
    )


@pytest.fixture
def extended_workflow_def():
    return ExtendedWorkflowDefAdapter(
        name=WORKFLOW_NAME,
        version=1,
        timeout_seconds=1,
        tasks=[
            WorkflowTaskAdapter(name=TASK_NAME, task_reference_name=WORKFLOW_TASK_REF)
        ],
    )


@pytest.fixture
def task_def():
    return TaskDefAdapter(name=TASK_NAME, timeout_seconds=1, total_timeout_seconds=1)


@pytest.fixture
def extended_task_def():
    return ExtendedTaskDefAdapter(
        name=TASK_NAME, timeout_seconds=1, total_timeout_seconds=1
    )


@pytest.fixture
def wf_tag_obj():
    return TagAdapter(key="test", type="METADATA", value="val")


def test_init(metadata_client):
    message = "metadata_api is not of type MetadataResourceApiAdapter"
    assert isinstance(metadata_client.metadata_api, MetadataResourceApiAdapter), message
    message = "tags_api is not of type TagsApi"
    assert isinstance(metadata_client.tags_api, TagsApiAdapter), message


@pytest.mark.asyncio
async def test_register_workflow_def(mocker, metadata_client, extended_workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "create")
    await metadata_client.register_workflow_def(extended_workflow_def)
    assert mock.called
    mock.assert_called_with(extended_workflow_def, overwrite=False, new_version=None)


@pytest.mark.asyncio
async def test_register_workflow_def_without_overwrite(
    mocker, metadata_client, extended_workflow_def
):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "create")
    await metadata_client.register_workflow_def(extended_workflow_def, overwrite=False)
    assert mock.called
    mock.assert_called_with(extended_workflow_def, overwrite=False, new_version=None)


@pytest.mark.asyncio
async def test_update_workflow_defs(mocker, metadata_client, extended_workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "update")
    workflow_defs = [extended_workflow_def]
    await metadata_client.update_workflow_defs(workflow_defs)
    assert mock.called
    mock.assert_called_with(workflow_defs, overwrite=None, new_version=None)


@pytest.mark.asyncio
async def test_update_workflow_defs_without_overwrite(
    mocker, metadata_client, extended_workflow_def
):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "update")
    workflow_defs = [extended_workflow_def]
    await metadata_client.update_workflow_defs(workflow_defs, overwrite=False)
    assert mock.called
    mock.assert_called_with(workflow_defs, overwrite=False, new_version=None)


@pytest.mark.asyncio
async def test_unregister_workflow_def(mocker, metadata_client):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "unregister_workflow_def")
    await metadata_client.unregister_workflow_def(WORKFLOW_NAME, 1)
    assert mock.called
    mock.assert_called_with(name=WORKFLOW_NAME, version=1)


@pytest.mark.asyncio
async def test_get_workflow_def_without_version(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get")
    mock.return_value = workflow_def
    wf = await metadata_client.get_workflow_def(WORKFLOW_NAME)
    assert wf == workflow_def
    assert mock.called
    mock.assert_called_with(name=WORKFLOW_NAME, version=None, metadata=None)


@pytest.mark.asyncio
async def test_get_workflow_def_with_version(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get")
    mock.return_value = workflow_def
    wf = await metadata_client.get_workflow_def(WORKFLOW_NAME, version=1)
    assert wf == workflow_def
    mock.assert_called_with(name=WORKFLOW_NAME, version=1, metadata=None)


@pytest.mark.asyncio
async def test_get_workflow_def_non_existent(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get")
    message = f"No such workflow found by name:{WORKFLOW_NAME}, version: null"
    error_body = {"status": 404, "message": message}
    mock.side_effect = mocker.MagicMock(
        side_effect=ApiException(status=404, body=json.dumps(error_body))
    )
    with pytest.raises(ApiException):
        await metadata_client.get_workflow_def(WORKFLOW_NAME)


@pytest.mark.asyncio
async def test_get_all_workflow_defs(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_workflow_defs")
    expected_workflow_defs_len = 2
    workflow_def2 = WorkflowDefAdapter(
        name="ut_wf_2",
        version=1,
        timeout_seconds=1,
        tasks=[
            WorkflowTaskAdapter(name=TASK_NAME, task_reference_name=WORKFLOW_TASK_REF)
        ],
    )
    mock.return_value = [workflow_def, workflow_def2]
    wfs = await metadata_client.get_all_workflow_defs()
    assert len(wfs) == expected_workflow_defs_len


@pytest.mark.asyncio
async def test_register_task_def(mocker, metadata_client, extended_task_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "register_task_def")
    await metadata_client.register_task_def(extended_task_def)
    assert mock.called
    mock.assert_called_with([extended_task_def])


@pytest.mark.asyncio
async def test_update_task_def(mocker, metadata_client, extended_task_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "update_task_def")
    await metadata_client.update_task_def(extended_task_def)
    assert mock.called
    mock.assert_called_with(extended_task_def=extended_task_def)


@pytest.mark.asyncio
async def test_unregister_task_def(mocker, metadata_client):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "unregister_task_def")
    await metadata_client.unregister_task_def(TASK_NAME)
    assert mock.called
    mock.assert_called_with(tasktype=TASK_NAME)


@pytest.mark.asyncio
async def test_get_task_def(mocker, metadata_client, task_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_task_def")
    mock.return_value = task_def
    task_definition = await metadata_client.get_task_def(TASK_NAME)
    assert task_definition == task_def
    mock.assert_called_with(TASK_NAME)


@pytest.mark.asyncio
async def test_get_all_task_defs(mocker, metadata_client, task_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_task_defs")
    expected_tasks_defs_len = 2
    task_def2 = TaskDefAdapter(
        name="ut_task2", timeout_seconds=1, total_timeout_seconds=1
    )
    mock.return_value = [task_def, task_def2]
    tasks = await metadata_client.get_all_task_defs()
    assert len(tasks) == expected_tasks_defs_len


@pytest.mark.asyncio
async def test_get_task_defs_with_filters(mocker, metadata_client, task_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_task_defs")
    mock.return_value = [task_def]
    tasks = await metadata_client.get_task_defs(
        access="EXECUTE", metadata=True, tag_key="test", tag_value="val"
    )
    mock.assert_called_with(
        access="EXECUTE", metadata=True, tag_key="test", tag_value="val"
    )
    assert len(tasks) == 1


@pytest.mark.asyncio
async def test_get_workflow_defs_with_filters(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_workflow_defs")
    mock.return_value = [workflow_def]
    workflows = await metadata_client.get_workflow_defs(
        access="EXECUTE",
        metadata=True,
        tag_key="test",
        tag_value="val",
        name="test_wf",
        short=True,
    )
    mock.assert_called_with(
        access="EXECUTE",
        metadata=True,
        tag_key="test",
        tag_value="val",
        name="test_wf",
        short=True,
    )
    assert len(workflows) == 1


@pytest.mark.asyncio
async def test_upload_definitions_to_s3(mocker, metadata_client):
    mock = mocker.patch.object(
        MetadataResourceApiAdapter, "upload_workflows_and_tasks_definitions_to_s3"
    )
    await metadata_client.upload_definitions_to_s3()
    assert mock.called


@pytest.mark.asyncio
async def test_get_latest_workflow_def(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get")
    mock.return_value = workflow_def
    wf = await metadata_client.get_latest_workflow_def(WORKFLOW_NAME)
    assert wf == workflow_def
    mock.assert_called_with(name=WORKFLOW_NAME, version=None, metadata=None)


@pytest.mark.asyncio
async def test_get_workflow_def_with_metadata(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get")
    mock.return_value = workflow_def
    wf = await metadata_client.get_workflow_def_with_metadata(WORKFLOW_NAME)
    assert wf == workflow_def
    mock.assert_called_with(name=WORKFLOW_NAME, version=None, metadata=True)


@pytest.mark.asyncio
async def test_get_task_defs_by_tag(mocker, metadata_client, task_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_task_defs")
    mock.return_value = [task_def]
    tasks = await metadata_client.get_task_defs_by_tag("test_key", "test_value")
    mock.assert_called_with(
        tag_key="test_key", tag_value="test_value", access=None, metadata=None
    )
    assert len(tasks) == 1


@pytest.mark.asyncio
async def test_get_workflow_defs_by_tag(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_workflow_defs")
    mock.return_value = [workflow_def]
    workflows = await metadata_client.get_workflow_defs_by_tag("test_key", "test_value")
    mock.assert_called_with(
        tag_key="test_key",
        tag_value="test_value",
        access=None,
        metadata=None,
        name=None,
        short=None,
    )
    assert len(workflows) == 1


@pytest.mark.asyncio
async def test_get_task_defs_with_metadata(mocker, metadata_client, task_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_task_defs")
    mock.return_value = [task_def]
    tasks = await metadata_client.get_task_defs_with_metadata()
    mock.assert_called_with(metadata=True, access=None, tag_key=None, tag_value=None)
    assert len(tasks) == 1


@pytest.mark.asyncio
async def test_get_workflow_defs_with_metadata(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_workflow_defs")
    mock.return_value = [workflow_def]
    workflows = await metadata_client.get_workflow_defs_with_metadata()
    mock.assert_called_with(
        metadata=True, access=None, tag_key=None, tag_value=None, name=None, short=None
    )
    assert len(workflows) == 1


@pytest.mark.asyncio
async def test_get_workflow_defs_by_name(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_workflow_defs")
    mock.return_value = [workflow_def]
    workflows = await metadata_client.get_workflow_defs_by_name(WORKFLOW_NAME)
    mock.assert_called_with(
        name=WORKFLOW_NAME,
        metadata=None,
        access=None,
        tag_key=None,
        tag_value=None,
        short=None,
    )
    assert len(workflows) == 1


@pytest.mark.asyncio
async def test_get_workflow_defs_short(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_workflow_defs")
    mock.return_value = [workflow_def]
    workflows = await metadata_client.get_workflow_defs_short()
    mock.assert_called_with(
        short=True,
        name=None,
        metadata=None,
        access=None,
        tag_key=None,
        tag_value=None,
    )
    assert len(workflows) == 1


@pytest.mark.asyncio
async def test_get_task_defs_by_access(mocker, metadata_client, task_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_task_defs")
    mock.return_value = [task_def]
    tasks = await metadata_client.get_task_defs_by_access("EXECUTE")
    mock.assert_called_with(
        access="EXECUTE",
        metadata=None,
        tag_key=None,
        tag_value=None,
    )
    assert len(tasks) == 1


@pytest.mark.asyncio
async def test_get_workflow_defs_by_access(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_workflow_defs")
    mock.return_value = [workflow_def]
    workflows = await metadata_client.get_workflow_defs_by_access("EXECUTE")
    mock.assert_called_with(
        access="EXECUTE",
        short=None,
        name=None,
        metadata=None,
        tag_key=None,
        tag_value=None,
    )
    assert len(workflows) == 1


@pytest.mark.asyncio
async def test_register_workflow_def_alias(
    mocker, metadata_client, extended_workflow_def
):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "create")
    await metadata_client.register_workflow_def(extended_workflow_def, overwrite=False)
    assert mock.called
    mock.assert_called_with(extended_workflow_def, overwrite=False, new_version=None)


@pytest.mark.asyncio
async def test_update_workflow_def_alias(
    mocker, metadata_client, extended_workflow_def
):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "create")
    await metadata_client.update_workflow_def(extended_workflow_def, overwrite=True)
    assert mock.called
    mock.assert_called_with(extended_workflow_def, overwrite=True, new_version=None)


@pytest.mark.asyncio
async def test_get_workflow_def_versions(mocker, metadata_client):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_workflow_defs")
    workflow_def1 = WorkflowDefAdapter(
        name=WORKFLOW_NAME,
        version=1,
        timeout_seconds=1,
        tasks=[
            WorkflowTaskAdapter(name=TASK_NAME, task_reference_name=WORKFLOW_TASK_REF)
        ],
    )
    workflow_def2 = WorkflowDefAdapter(
        name=WORKFLOW_NAME,
        version=2,
        timeout_seconds=1,
        tasks=[
            WorkflowTaskAdapter(name=TASK_NAME, task_reference_name=WORKFLOW_TASK_REF)
        ],
    )
    mock.return_value = [workflow_def1, workflow_def2]
    versions = await metadata_client.get_workflow_def_versions(WORKFLOW_NAME)
    mock.assert_called_with(
        name=WORKFLOW_NAME,
        access=None,
        metadata=None,
        short=None,
        tag_key=None,
        tag_value=None,
    )
    assert versions == [1, 2]


@pytest.mark.asyncio
async def test_get_workflow_def_latest_version(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get")
    mock.return_value = workflow_def
    wf = await metadata_client.get_workflow_def_latest_version(WORKFLOW_NAME)
    assert wf == workflow_def
    mock.assert_called_with(name=WORKFLOW_NAME, version=None, metadata=None)


@pytest.mark.asyncio
async def test_get_workflow_def_latest_versions(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_workflow_defs")
    mock.return_value = [workflow_def]
    workflows = await metadata_client.get_workflow_def_latest_versions()
    mock.assert_called_with(
        name=None, access=None, metadata=None, short=None, tag_key=None, tag_value=None
    )
    assert len(workflows) == 1


@pytest.mark.asyncio
async def test_get_workflow_def_by_version(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get")
    mock.return_value = workflow_def
    wf = await metadata_client.get_workflow_def_by_version(WORKFLOW_NAME, 1)
    assert wf == workflow_def
    mock.assert_called_with(name=WORKFLOW_NAME, version=1, metadata=None)


@pytest.mark.asyncio
async def test_get_workflow_def_by_name(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_workflow_defs")
    mock.return_value = [workflow_def]
    workflows = await metadata_client.get_workflow_def_by_name(WORKFLOW_NAME)
    mock.assert_called_with(
        name=WORKFLOW_NAME,
        access=None,
        metadata=None,
        short=None,
        tag_key=None,
        tag_value=None,
    )
    assert len(workflows) == 1


@pytest.mark.asyncio
async def test_register_task_def_validated(mocker, metadata_client, extended_task_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "register_task_def")
    await metadata_client.register_task_def_validated([extended_task_def])
    mock.assert_called_with(extended_task_def=[extended_task_def])


@pytest.mark.asyncio
async def test_get_task_def_validated(mocker, metadata_client, task_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "get_task_def")
    task_dict = {
        "name": TASK_NAME,
        "timeoutSeconds": 1,
        "totalTimeoutSeconds": 1,
    }
    mock.return_value = task_dict
    task = await metadata_client.get_task_def_validated(TASK_NAME)
    mock.assert_called_with(tasktype=TASK_NAME)
    assert task.name == TASK_NAME


@pytest.mark.asyncio
async def test_create_workflow_def_validated(mocker, metadata_client, extended_workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "create")
    await metadata_client.create_workflow_def_validated(extended_workflow_def)
    mock.assert_called_with(extended_workflow_def, overwrite=None, new_version=None)


@pytest.mark.asyncio
async def test_create_workflow_def_validated_with_params(mocker, metadata_client, extended_workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "create")
    await metadata_client.create_workflow_def_validated(extended_workflow_def, overwrite=True, new_version=False)
    mock.assert_called_with(extended_workflow_def, overwrite=True, new_version=False)


@pytest.mark.asyncio
async def test_update_workflow_defs_validated(mocker, metadata_client, extended_workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "update")
    await metadata_client.update_workflow_defs_validated([extended_workflow_def])
    mock.assert_called_with(extended_workflow_def=[extended_workflow_def], overwrite=None, new_version=None)


@pytest.mark.asyncio
async def test_update_workflow_defs_validated_with_params(mocker, metadata_client, extended_workflow_def):
    mock = mocker.patch.object(MetadataResourceApiAdapter, "update")
    await metadata_client.update_workflow_defs_validated([extended_workflow_def], overwrite=True, new_version=False)
    mock.assert_called_with(extended_workflow_def=[extended_workflow_def], overwrite=True, new_version=False)


@pytest.mark.asyncio
async def test_register_workflow_def_validated(mocker, metadata_client, extended_workflow_def):
    mock = mocker.patch.object(metadata_client, "create_workflow_def_validated")
    await metadata_client.register_workflow_def_validated(extended_workflow_def)
    mock.assert_called_with(extended_workflow_def=extended_workflow_def, overwrite=False)


@pytest.mark.asyncio
async def test_update_workflow_def_validated(mocker, metadata_client, extended_workflow_def):
    mock = mocker.patch.object(metadata_client, "create_workflow_def_validated")
    await metadata_client.update_workflow_def_validated(extended_workflow_def)
    mock.assert_called_with(extended_workflow_def=extended_workflow_def, overwrite=True)
