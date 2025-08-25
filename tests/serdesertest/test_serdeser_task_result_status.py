import json

import pytest

from conductor.client.adapters.models.task_result_adapter import TaskResultAdapter
from conductor.shared.http.enums import TaskResultStatus
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("TaskResult"))


def test_task_result_serde(server_json):
    task_result = TaskResultAdapter()
    task_result.workflow_instance_id = server_json.get("workflowInstanceId")
    task_result.task_id = server_json.get("taskId")
    task_result.reason_for_incompletion = server_json.get("reasonForIncompletion")
    task_result.callback_after_seconds = server_json.get("callbackAfterSeconds", 0)
    task_result.worker_id = server_json.get("workerId")
    status_str = server_json.get("status")
    if status_str:
        task_result.status = TaskResultStatus[status_str]
    task_result.output_data = server_json.get("outputData", {})
    logs_json = server_json.get("logs", [])
    for log_entry in logs_json:
        if isinstance(log_entry, dict) and "log" in log_entry:
            task_result.log(log_entry["log"])
    task_result.external_output_payload_storage_path = server_json.get(
        "externalOutputPayloadStoragePath"
    )
    task_result.sub_workflow_id = server_json.get("subWorkflowId")
    task_result.extend_lease = server_json.get("extendLease", False)
    assert task_result.workflow_instance_id == server_json.get("workflowInstanceId")
    assert task_result.task_id == server_json.get("taskId")
    assert task_result.reason_for_incompletion == server_json.get(
        "reasonForIncompletion"
    )
    assert task_result.callback_after_seconds == server_json.get(
        "callbackAfterSeconds", 0
    )
    assert task_result.worker_id == server_json.get("workerId")
    if status_str:
        assert task_result.status.name == status_str
    assert task_result.output_data == server_json.get("outputData", {})
    assert len(task_result.logs) == len(logs_json)
    for i, log_entry in enumerate(logs_json):
        if isinstance(log_entry, dict) and "log" in log_entry:
            assert task_result.logs[i].log == log_entry["log"]
    assert task_result.external_output_payload_storage_path == server_json.get(
        "externalOutputPayloadStoragePath"
    )
    assert task_result.sub_workflow_id == server_json.get("subWorkflowId")
    assert task_result.extend_lease == server_json.get("extendLease", False)
    serialized_dict = task_result.to_dict()
    fields_to_check = [
        ("workflowInstanceId", "workflowInstanceId"),
        ("workflow_instance_id", "workflowInstanceId"),
        ("taskId", "taskId"),
        ("task_id", "taskId"),
        ("reasonForIncompletion", "reasonForIncompletion"),
        ("reason_for_incompletion", "reasonForIncompletion"),
        ("callbackAfterSeconds", "callbackAfterSeconds"),
        ("callback_after_seconds", "callbackAfterSeconds"),
        ("workerId", "workerId"),
        ("worker_id", "workerId"),
        ("externalOutputPayloadStoragePath", "externalOutputPayloadStoragePath"),
        ("external_output_payload_storage_path", "externalOutputPayloadStoragePath"),
        ("subWorkflowId", "subWorkflowId"),
        ("sub_workflow_id", "subWorkflowId"),
        ("extendLease", "extendLease"),
        ("extend_lease", "extendLease"),
    ]
    for serialized_key, server_key in fields_to_check:
        if serialized_key in serialized_dict:
            assert serialized_dict[serialized_key] == server_json.get(server_key)
    status_keys = ["status", "_status"]
    for key in status_keys:
        if key in serialized_dict and serialized_dict[key] is not None and status_str:
            if isinstance(serialized_dict[key], str):
                assert serialized_dict[key] == status_str
            else:
                assert serialized_dict[key].name == status_str
    output_data_keys = ["outputData", "output_data", "_output_data"]
    for key in output_data_keys:
        if key in serialized_dict:
            assert serialized_dict[key] == server_json.get("outputData", {})
    logs_keys = ["logs", "_logs"]
    for key in logs_keys:
        if key in serialized_dict:
            assert len(serialized_dict[key]) == len(logs_json)
