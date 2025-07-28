import json

import pytest

from conductor.client.http.models.task_summary import TaskSummary
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("TaskSummary")
    return json.loads(server_json_str)


def test_task_summary_ser_deser(server_json):
    # 1. Deserialize JSON to TaskSummary object
    task_summary = TaskSummary(
        workflow_id=server_json.get("workflowId"),
        workflow_type=server_json.get("workflowType"),
        correlation_id=server_json.get("correlationId"),
        scheduled_time=server_json.get("scheduledTime"),
        start_time=server_json.get("startTime"),
        update_time=server_json.get("updateTime"),
        end_time=server_json.get("endTime"),
        status=server_json.get("status"),
        reason_for_incompletion=server_json.get("reasonForIncompletion"),
        execution_time=server_json.get("executionTime"),
        queue_wait_time=server_json.get("queueWaitTime"),
        task_def_name=server_json.get("taskDefName"),
        task_type=server_json.get("taskType"),
        input=server_json.get("input"),
        output=server_json.get("output"),
        task_id=server_json.get("taskId"),
        external_input_payload_storage_path=server_json.get(
            "externalInputPayloadStoragePath"
        ),
        external_output_payload_storage_path=server_json.get(
            "externalOutputPayloadStoragePath"
        ),
        workflow_priority=server_json.get("workflowPriority"),
        domain=server_json.get("domain"),
    )
    # 2. Verify all fields are properly populated
    assert server_json.get("workflowId") == task_summary.workflow_id
    assert server_json.get("workflowType") == task_summary.workflow_type
    assert server_json.get("correlationId") == task_summary.correlation_id
    assert server_json.get("scheduledTime") == task_summary.scheduled_time
    assert server_json.get("startTime") == task_summary.start_time
    assert server_json.get("updateTime") == task_summary.update_time
    assert server_json.get("endTime") == task_summary.end_time
    assert server_json.get("status") == task_summary.status
    assert (
        server_json.get("reasonForIncompletion") == task_summary.reason_for_incompletion
    )
    assert server_json.get("executionTime") == task_summary.execution_time
    assert server_json.get("queueWaitTime") == task_summary.queue_wait_time
    assert server_json.get("taskDefName") == task_summary.task_def_name
    assert server_json.get("taskType") == task_summary.task_type
    assert server_json.get("input") == task_summary.input
    assert server_json.get("output") == task_summary.output
    assert server_json.get("taskId") == task_summary.task_id
    assert (
        server_json.get("externalInputPayloadStoragePath")
        == task_summary.external_input_payload_storage_path
    )
    assert (
        server_json.get("externalOutputPayloadStoragePath")
        == task_summary.external_output_payload_storage_path
    )
    assert server_json.get("workflowPriority") == task_summary.workflow_priority
    assert server_json.get("domain") == task_summary.domain
    # 3. Serialize TaskSummary back to JSON
    serialized_json = task_summary.to_dict()
    # 4. Verify serialized JSON matches original
    # Check that all fields from original JSON are present in serialized JSON
    for json_key, json_value in server_json.items():
        # Convert camelCase to snake_case for comparison
        python_key = "".join(["_" + c.lower() if c.isupper() else c for c in json_key])
        python_key = python_key.lstrip("_")
        # Get the corresponding value from serialized JSON
        assert python_key in serialized_json
        assert json_value == serialized_json[python_key]
    # Check that all fields from serialized JSON are present in original JSON
    for python_key, python_value in serialized_json.items():
        # Convert snake_case to camelCase for comparison
        parts = python_key.split("_")
        json_key = parts[0] + "".join(x.title() for x in parts[1:])
        # Get the corresponding value from original JSON
        assert json_key in server_json
        assert python_value == server_json[json_key]
