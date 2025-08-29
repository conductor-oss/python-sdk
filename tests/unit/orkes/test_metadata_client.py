import json
import logging

import pytest

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api import MetadataResourceApi
from conductor.client.http.models.tag_string import TagStringAdapter as TagString
from conductor.client.http.models.task_def import TaskDefAdapter as TaskDef
from conductor.client.http.models.workflow_def import WorkflowDefAdapter as WorkflowDef
from conductor.client.codegen.rest import ApiException
from conductor.client.orkes.api.tags_api import TagsApi
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.models.ratelimit_tag import RateLimitTag
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient

WORKFLOW_NAME = "ut_wf"
TASK_NAME = "ut_task"


@pytest.fixture(scope="module")
def metadata_client():
    configuration = Configuration("http://localhost:8080/api")
    return OrkesMetadataClient(configuration)


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def workflow_def():
    return WorkflowDef(name=WORKFLOW_NAME, version=1)


@pytest.fixture
def task_def():
    return TaskDef(TASK_NAME)


@pytest.fixture
def wf_tag_obj():
    return MetadataTag("test", "val")


def test_init(metadata_client):
    message = "metadataResourceApi is not of type MetadataResourceApi"
    assert isinstance(metadata_client.metadataResourceApi, MetadataResourceApi), message


def test_register_workflow_def(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApi, "create")
    metadata_client.register_workflow_def(workflow_def)
    assert mock.called
    mock.assert_called_with(workflow_def, overwrite=True)


def test_register_workflow_def_without_overwrite(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApi, "create")
    metadata_client.register_workflow_def(workflow_def, False)
    assert mock.called
    mock.assert_called_with(workflow_def, overwrite=False)


def test_update_workflow_def(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApi, "update")
    metadata_client.update_workflow_def(workflow_def)
    assert mock.called
    mock.assert_called_with([workflow_def], overwrite=True)


def test_update_workflow_def_without_overwrite(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApi, "update")
    metadata_client.update_workflow_def(workflow_def, False)
    assert mock.called
    mock.assert_called_with([workflow_def], overwrite=False)


def test_unregister_workflow_def(mocker, metadata_client):
    mock = mocker.patch.object(MetadataResourceApi, "unregister_workflow_def")
    metadata_client.unregister_workflow_def(WORKFLOW_NAME, 1)
    assert mock.called
    mock.assert_called_with(WORKFLOW_NAME, 1)


def test_get_workflow_def_without_version(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApi, "get1")
    mock.return_value = workflow_def
    wf = metadata_client.get_workflow_def(WORKFLOW_NAME)
    assert wf == workflow_def
    assert mock.called
    mock.assert_called_with(WORKFLOW_NAME)


def test_get_workflow_def_with_version(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApi, "get1")
    mock.return_value = workflow_def
    wf = metadata_client.get_workflow_def(WORKFLOW_NAME, 1)
    assert wf == workflow_def
    mock.assert_called_with(WORKFLOW_NAME, version=1)


def test_get_workflow_def_non_existent(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApi, "get1")
    message = f"No such workflow found by name:{WORKFLOW_NAME}, version: null"
    error_body = {"status": 404, "message": message}
    mock.side_effect = mocker.MagicMock(
        side_effect=ApiException(status=404, body=json.dumps(error_body))
    )
    with pytest.raises(ApiException):
        metadata_client.get_workflow_def(WORKFLOW_NAME)


def test_get_all_workflow_defs(mocker, metadata_client, workflow_def):
    mock = mocker.patch.object(MetadataResourceApi, "get_workflow_defs")
    expected_workflow_defs_len = 2
    workflow_def2 = WorkflowDef(name="ut_wf_2", version=1)
    mock.return_value = [workflow_def, workflow_def2]
    wfs = metadata_client.get_all_workflow_defs()
    assert len(wfs) == expected_workflow_defs_len


def test_register_task_def(mocker, metadata_client, task_def):
    mock = mocker.patch.object(MetadataResourceApi, "register_task_def")
    metadata_client.register_task_def(task_def)
    assert mock.called
    mock.assert_called_with([task_def])


def test_update_task_def(mocker, metadata_client, task_def):
    mock = mocker.patch.object(MetadataResourceApi, "update_task_def")
    metadata_client.update_task_def(task_def)
    assert mock.called
    mock.assert_called_with(task_def)


def test_unregister_task_def(mocker, metadata_client):
    mock = mocker.patch.object(MetadataResourceApi, "unregister_task_def")
    metadata_client.unregister_task_def(TASK_NAME)
    assert mock.called
    mock.assert_called_with(TASK_NAME)


def test_get_task_def(mocker, metadata_client, task_def):
    mock = mocker.patch.object(MetadataResourceApi, "get_task_def")
    mock.return_value = task_def
    task_definition = metadata_client.get_task_def(TASK_NAME)
    assert task_definition == task_def
    mock.assert_called_with(TASK_NAME)


def test_get_all_task_defs(mocker, metadata_client, task_def):
    mock = mocker.patch.object(MetadataResourceApi, "get_task_defs")
    expected_tasks_defs_len = 2
    task_def2 = TaskDef("ut_task2")
    mock.return_value = [task_def, task_def2]
    tasks = metadata_client.get_all_task_defs()
    assert len(tasks) == expected_tasks_defs_len


def test_add_workflow_tag(mocker, metadata_client, wf_tag_obj):
    mock = mocker.patch.object(TagsApi, "add_workflow_tag")
    metadata_client.add_workflow_tag(wf_tag_obj, WORKFLOW_NAME)
    mock.assert_called_with(wf_tag_obj, WORKFLOW_NAME)


def test_delete_workflow_tag(mocker, metadata_client, wf_tag_obj):
    mock = mocker.patch.object(TagsApi, "delete_workflow_tag")
    wf_tag_str = TagString("test", "METADATA", "val")
    metadata_client.delete_workflow_tag(wf_tag_obj, WORKFLOW_NAME)
    mock.assert_called_with(wf_tag_str, WORKFLOW_NAME)


def test_set_workflow_tags(mocker, metadata_client, wf_tag_obj):
    mock = mocker.patch.object(TagsApi, "set_workflow_tags")
    wf_tag_obj2 = MetadataTag("test2", "val2")
    wf_tag_objs = [wf_tag_obj, wf_tag_obj2]
    metadata_client.set_workflow_tags(wf_tag_objs, WORKFLOW_NAME)
    mock.assert_called_with(wf_tag_objs, WORKFLOW_NAME)


def test_get_workflow_tags(mocker, metadata_client, wf_tag_obj):
    mock = mocker.patch.object(TagsApi, "get_workflow_tags")
    expected_tags_len = 2
    wf_tag_obj2 = MetadataTag("test2", "val2")
    mock.return_value = [wf_tag_obj, wf_tag_obj2]
    tags = metadata_client.get_workflow_tags(WORKFLOW_NAME)
    mock.assert_called_with(WORKFLOW_NAME)
    assert len(tags) == expected_tags_len


def test_add_task_tag(mocker, metadata_client):
    mock = mocker.patch.object(TagsApi, "add_task_tag")
    task_tag = MetadataTag("tag1", "val1")
    metadata_client.addTaskTag(task_tag, TASK_NAME)
    mock.assert_called_with(task_tag, TASK_NAME)


def test_delete_task_tag(mocker, metadata_client):
    mock = mocker.patch.object(TagsApi, "delete_task_tag")
    task_tag = MetadataTag("tag1", "val1")
    task_tag_str = TagString("tag1", "METADATA", "val1")
    metadata_client.deleteTaskTag(task_tag, TASK_NAME)
    mock.assert_called_with(task_tag_str, TASK_NAME)


def test_set_task_tags(mocker, metadata_client):
    mock = mocker.patch.object(TagsApi, "set_task_tags")
    task_tag1 = MetadataTag("tag1", "val1")
    task_tag2 = MetadataTag("tag2", "val2")
    task_tag_objs = [task_tag1, task_tag2]
    metadata_client.setTaskTags(task_tag_objs, TASK_NAME)
    mock.assert_called_with(task_tag_objs, TASK_NAME)


def test_get_task_tags(mocker, metadata_client):
    mock = mocker.patch.object(TagsApi, "get_task_tags")
    expected_tags_len = 2
    task_tag1 = MetadataTag("tag1", "val1")
    task_tag2 = MetadataTag("tag2", "val2")
    mock.return_value = [task_tag1, task_tag2]
    tags = metadata_client.getTaskTags(TASK_NAME)
    mock.assert_called_with(TASK_NAME)
    assert len(tags) == expected_tags_len


def test_set_workflow_rate_limit(mocker, metadata_client):
    mock_set = mocker.patch.object(TagsApi, "add_workflow_tag")
    mock_remove = mocker.patch.object(TagsApi, "get_workflow_tags")
    mock_remove.return_value = []
    rate_limit_tag = RateLimitTag(WORKFLOW_NAME, 5)
    metadata_client.setWorkflowRateLimit(5, WORKFLOW_NAME)
    mock_remove.assert_called_with(WORKFLOW_NAME)
    mock_set.assert_called_with(rate_limit_tag, WORKFLOW_NAME)


def test_get_workflow_rate_limit(mocker, metadata_client):
    mock = mocker.patch.object(TagsApi, "get_workflow_tags")
    expected_workflow_rate_limit = 5
    metadata_tag = MetadataTag("test", "val")
    rate_limit_tag = RateLimitTag(WORKFLOW_NAME, 5)
    mock.return_value = [metadata_tag, rate_limit_tag]
    rate_limit = metadata_client.getWorkflowRateLimit(WORKFLOW_NAME)
    assert rate_limit == expected_workflow_rate_limit


def test_get_workflow_rate_limit_not_set(mocker, metadata_client):
    mock = mocker.patch.object(TagsApi, "get_workflow_tags")
    mock.return_value = []
    rate_limit = metadata_client.getWorkflowRateLimit(WORKFLOW_NAME)
    mock.assert_called_with(WORKFLOW_NAME)
    assert rate_limit is None


def test_remove_workflow_rate_limit(mocker, metadata_client):
    patched_tags_api = mocker.patch.object(TagsApi, "delete_workflow_tag")
    patched_metadata_client = mocker.patch.object(
        OrkesMetadataClient, "getWorkflowRateLimit"
    )
    patched_metadata_client.return_value = 5
    metadata_client.removeWorkflowRateLimit(WORKFLOW_NAME)
    rate_limit_tag = RateLimitTag(WORKFLOW_NAME, 5)
    patched_tags_api.assert_called_with(rate_limit_tag, WORKFLOW_NAME)
