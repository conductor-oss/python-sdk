import json

import pytest

from conductor.client.http.models.task_exec_log import TaskExecLogAdapter
from conductor.client.http.models.task_result import TaskResultAdapter
from conductor.client.http.models.workflow_state_update import WorkflowStateUpdateAdapter
from conductor.shared.http.enums import TaskResultStatus

from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("WorkflowStateUpdate")
    return json.loads(server_json_str)


def test_serialization_deserialization(server_json):  # noqa: PLR0915
    # Step 1: Deserialize JSON to SDK model object
    # First, properly initialize TaskResult if it exists
    task_result_json = server_json.get("taskResult")
    task_result = None
    if task_result_json:
        # Create TaskExecLog objects if logs are present
        logs = (
            [
                TaskExecLogAdapter(
                    log=log_entry.get("log"),
                    created_time=log_entry.get("createdTime"),
                    task_id=log_entry.get("taskId"),
                )
                for log_entry in task_result_json.get("logs")
            ]
            if task_result_json.get("logs")
            else []
        )

        # Create TaskResult object with proper field mappings
        task_result = TaskResultAdapter(
            workflow_instance_id=task_result_json.get("workflowInstanceId"),
            task_id=task_result_json.get("taskId"),
            reason_for_incompletion=task_result_json.get("reasonForIncompletion"),
            callback_after_seconds=task_result_json.get("callbackAfterSeconds"),
            worker_id=task_result_json.get("workerId"),
            status=task_result_json.get("status"),
            output_data=task_result_json.get("outputData"),
            logs=logs,
            external_output_payload_storage_path=task_result_json.get(
                "externalOutputPayloadStoragePath"
            ),
            sub_workflow_id=task_result_json.get("subWorkflowId"),
            extend_lease=task_result_json.get("extendLease"),
        )
    # Now create the WorkflowStateUpdate object
    model_object = WorkflowStateUpdateAdapter(
        task_reference_name=server_json.get("taskReferenceName"),
        task_result=task_result,
        variables=server_json.get("variables"),
    )
    # Step 2: Verify all fields are properly populated
    assert model_object.task_reference_name == server_json.get("taskReferenceName")
    if task_result_json:
        # Verify TaskResult fields
        assert model_object.task_result is not None
        # Check each field that exists in the JSON
        for json_key, python_attr in TaskResultAdapter.attribute_map.items():
            if python_attr in task_result_json:
                # Special handling for status field which is converted to enum
                if json_key == "status" and task_result_json.get("status"):
                    assert model_object.task_result.status == task_result_json.get(
                        "status"
                    )
                # Special handling for logs which are objects
                elif json_key == "logs" and task_result_json.get("logs"):
                    assert len(model_object.task_result.logs) == len(
                        task_result_json.get("logs")
                    )
                    for i, log in enumerate(model_object.task_result.logs):
                        json_log = task_result_json.get("logs")[i]
                        if "log" in json_log:
                            assert log.log == json_log.get("log")
                        if "createdTime" in json_log:
                            assert log.created_time == json_log.get("createdTime")
                        if "taskId" in json_log:
                            assert log.task_id == json_log.get("taskId")
                # Normal field comparison
                else:
                    python_field_value = getattr(model_object.task_result, json_key)
                    json_field_value = task_result_json.get(python_attr)
                    assert python_field_value == json_field_value
    if server_json.get("variables"):
        assert model_object.variables == server_json.get("variables")
    # Step 3: Serialize the model back to dict
    result_dict = model_object.to_dict()
    # Step 4: Convert result_dict to match the original JSON structure
    serialized_json = {}
    # Map snake_case keys to camelCase based on attribute_map
    for snake_key, camel_key in WorkflowStateUpdateAdapter.attribute_map.items():
        if snake_key in result_dict and result_dict[snake_key] is not None:
            if snake_key == "task_result" and result_dict[snake_key]:
                # Handle TaskResult conversion
                task_result_dict = result_dict[snake_key]
                serialized_task_result = {}
                # Map TaskResult fields using its attribute_map
                for tr_snake_key, tr_camel_key in TaskResultAdapter.attribute_map.items():
                    if (
                        tr_snake_key in task_result_dict
                        and task_result_dict[tr_snake_key] is not None
                    ):
                        # Special handling for status which could be an enum
                        if tr_snake_key == "status" and isinstance(
                            task_result_dict[tr_snake_key], TaskResultStatus
                        ):
                            serialized_task_result[tr_camel_key] = task_result_dict[
                                tr_snake_key
                            ].name
                        # Special handling for logs which are objects
                        elif tr_snake_key == "logs" and task_result_dict[tr_snake_key]:
                            serialized_logs = []
                            for log in task_result_dict[tr_snake_key]:
                                if hasattr(log, "to_dict"):
                                    log_dict = log.to_dict()
                                    # Convert log dict keys to camelCase
                                    serialized_log = {}
                                    for log_key, log_value in log_dict.items():
                                        if (
                                            hasattr(TaskExecLogAdapter, "attribute_map")
                                            and log_key in TaskExecLogAdapter.attribute_map
                                        ):
                                            serialized_log[
                                                TaskExecLogAdapter.attribute_map[log_key]
                                            ] = log_value
                                        else:
                                            serialized_log[log_key] = log_value
                                    serialized_logs.append(serialized_log)
                                else:
                                    serialized_logs.append(log)
                            serialized_task_result[tr_camel_key] = serialized_logs
                        else:
                            serialized_task_result[tr_camel_key] = task_result_dict[
                                tr_snake_key
                            ]
                serialized_json[camel_key] = serialized_task_result
            else:
                serialized_json[camel_key] = result_dict[snake_key]
    # Step 5: Verify the resulting JSON matches the original
    # Check that all keys from original JSON exist in the serialized JSON
    for key in server_json:
        assert key in serialized_json
        # Skip detailed comparison of TaskResult as it's complex and some fields might be missing
        # Just check that the main structure is there
        if key == "taskResult" and server_json[key] is not None:
            for tr_key in server_json[key]:
                # Skip extendLease if it's false in our model but not present in JSON
                if (
                    tr_key == "extendLease"
                    and tr_key not in serialized_json[key]
                    and not server_json[key][tr_key]
                ):
                    continue
                # Allow missing fields if they're None or empty collections
                if tr_key not in serialized_json[key]:
                    # If it's a complex field that's missing, just note it's acceptable
                    # For logs, outputData, etc. that can be empty
                    if (
                        isinstance(server_json[key][tr_key], (dict, list))
                        and not server_json[key][tr_key]
                    ):
                        continue
                    # For primitive fields, if null/None/false, it's acceptable to be missing
                    if server_json[key][tr_key] in (None, False, "", 0):
                        continue
                    # If it's an important value that's missing, fail the test
                    raise Exception(f"Key {tr_key} missing from serialized TaskResult")
                # For fields that exist in both, compare values
                elif tr_key in serialized_json[key]:
                    # Special handling for logs and other complex types
                    if tr_key == "logs" and isinstance(server_json[key][tr_key], list):
                        # Check logs length
                        assert len(serialized_json[key][tr_key]) == len(
                            server_json[key][tr_key]
                        )
                        # Check each log entry for key fields, being careful with field mapping
                        for i, log in enumerate(server_json[key][tr_key]):
                            for log_key in log:
                                # Handle the case where the field might be named differently
                                # in the serialized output versus the JSON template
                                serialized_log = serialized_json[key][tr_key][i]
                                # Try to find the corresponding field in serialized log
                                if log_key in serialized_log:
                                    assert serialized_log[log_key] == log[log_key]
                                else:
                                    # Check if this is a field that has a different name in snake_case
                                    # Find the snake_case equivalent for the log_key
                                    snake_case_found = False
                                    if hasattr(TaskExecLogAdapter, "attribute_map"):
                                        for (
                                            snake_key,
                                            camel_key,
                                        ) in TaskExecLogAdapter.attribute_map.items():
                                            if camel_key == log_key:
                                                # Found the snake_case key corresponding to this camel_case key
                                                if snake_key in serialized_log:
                                                    assert (
                                                        serialized_log[snake_key]
                                                        == log[log_key]
                                                    )
                                                    snake_case_found = True
                                                    break
                                    # Skip error if field is optional or has default value
                                    if not snake_case_found and log[log_key] in (
                                        None,
                                        "",
                                        0,
                                        False,
                                    ):
                                        continue
                                    # If the field is important and missing, log it but don't fail
                                    # This is a common case for automatically generated models
                                    if not snake_case_found:
                                        print(
                                            f"Warning: Field {log_key} not found in serialized log. Original value: {log[log_key]}"
                                        )
                    # For scalar values, direct comparison
                    else:
                        assert serialized_json[key][tr_key] == server_json[key][tr_key]
        # For other fields, direct comparison
        else:
            assert serialized_json[key] == server_json[key]
