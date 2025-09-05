import json
import re

import pytest

from conductor.client.http.models.task import TaskAdapter
from conductor.client.http.models.workflow import WorkflowAdapter
from conductor.client.http.models.workflow_def import WorkflowDefAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("Workflow")
    return json.loads(server_json_str)


def test_workflow_serde(server_json):
    # 1. Create a complete workflow object from JSON
    workflow = create_workflow_from_json(server_json)
    # 2. Verify all fields are properly populated
    verify_workflow_fields(workflow, server_json)
    # 3. Serialize back to JSON
    result_json = workflow.to_dict()
    # 4. Compare original and resulting JSON
    compare_json_objects(server_json, result_json)


def create_workflow_from_json(json_data):
    """Create a Workflow object with all fields from JSON"""
    # Handle tasks if present
    tasks = None
    if json_data.get("tasks"):
        tasks = [
            create_task_from_json(task_json) for task_json in json_data.get("tasks")
        ]
    # Handle workflow definition if present
    workflow_def = None
    if json_data.get("workflowDefinition"):
        workflow_def = create_workflow_def_from_json(
            json_data.get("workflowDefinition")
        )
    # Handle sets
    failed_ref_tasks = set(json_data.get("failedReferenceTaskNames", []))
    failed_tasks = set(json_data.get("failedTaskNames", []))
    # Handle history if present
    history = None
    if json_data.get("history"):
        history = [
            create_workflow_from_json(wf_json) for wf_json in json_data.get("history")
        ]
    # Create the workflow with all fields
    return WorkflowAdapter(
        owner_app=json_data.get("ownerApp"),
        create_time=json_data.get("createTime"),
        update_time=json_data.get("updateTime"),
        created_by=json_data.get("createdBy"),
        updated_by=json_data.get("updatedBy"),
        status=json_data.get("status"),
        end_time=json_data.get("endTime"),
        workflow_id=json_data.get("workflowId"),
        parent_workflow_id=json_data.get("parentWorkflowId"),
        parent_workflow_task_id=json_data.get("parentWorkflowTaskId"),
        tasks=tasks,
        input=json_data.get("input"),
        output=json_data.get("output"),
        correlation_id=json_data.get("correlationId"),
        re_run_from_workflow_id=json_data.get("reRunFromWorkflowId"),
        reason_for_incompletion=json_data.get("reasonForIncompletion"),
        event=json_data.get("event"),
        task_to_domain=json_data.get("taskToDomain"),
        failed_reference_task_names=failed_ref_tasks,
        workflow_definition=workflow_def,
        external_input_payload_storage_path=json_data.get(
            "externalInputPayloadStoragePath"
        ),
        external_output_payload_storage_path=json_data.get(
            "externalOutputPayloadStoragePath"
        ),
        priority=json_data.get("priority"),
        variables=json_data.get("variables"),
        last_retried_time=json_data.get("lastRetriedTime"),
        failed_task_names=failed_tasks,
        history=history,
        idempotency_key=json_data.get("idempotencyKey"),
        rate_limit_key=json_data.get("rateLimitKey"),
        rate_limited=json_data.get("rateLimited"),
        start_time=json_data.get("startTime"),
        workflow_name=json_data.get("workflowName"),
        workflow_version=json_data.get("workflowVersion"),
    )


def create_task_from_json(task_json):
    """Create a Task object from JSON"""
    # Create a Task object with fields from task_json
    task = TaskAdapter()
    # Access all possible fields from task_json and set them on the task object
    for py_field, json_field in TaskAdapter.attribute_map.items():
        if json_field in task_json:
            setattr(task, py_field, task_json.get(json_field))
    return task


def create_workflow_def_from_json(workflow_def_json):
    """Create a WorkflowDef object from JSON"""
    # Create a WorkflowDef object with fields from workflow_def_json
    workflow_def = WorkflowDefAdapter()
    # Access all possible fields from workflow_def_json and set them on the workflow_def object
    for py_field, json_field in WorkflowDefAdapter.attribute_map.items():
        if json_field in workflow_def_json:
            # Special handling for nested objects or complex types could be added here
            setattr(workflow_def, py_field, workflow_def_json.get(json_field))
    return workflow_def


def verify_workflow_fields(workflow, json_data):
    """Verify that all fields in the Workflow object match the JSON data"""
    # Check all fields defined in the model
    for py_field, json_field in WorkflowAdapter.attribute_map.items():
        if json_field in json_data:
            python_value = getattr(workflow, py_field)
            json_value = json_data.get(json_field)
            # Skip complex objects that need special handling
            if py_field in ["tasks", "workflow_definition", "history"]:
                continue
            # Handle sets which need conversion
            if (
                py_field in ["failed_reference_task_names", "failed_task_names"]
                and json_value
            ):
                assert set(python_value) == set(json_value)
                continue
            # Handle dictionaries and other simple types
            assert python_value == json_value, f"Field {py_field} doesn't match"


def compare_json_objects(original, result):
    """Compare original and resulting JSON objects"""
    # For each field in the original JSON
    for key in original:
        if key in result:
            # Handle sets vs lists conversion for known set fields
            if key in ["failedReferenceTaskNames", "failedTaskNames"]:
                if isinstance(original[key], list) and isinstance(
                    result[key], (list, set)
                ):
                    assert set(original[key]) == set(
                        result[key]
                    ), f"Field {key} doesn't match after set conversion"
                continue
            # If it's a nested object
            if isinstance(original[key], dict) and isinstance(result[key], dict):
                compare_json_objects(original[key], result[key])
            # If it's a list
            elif isinstance(original[key], list) and isinstance(result[key], list):
                assert len(original[key]) == len(result[key])
                # For complex objects in lists, we could add recursive comparison
            # Simple value
            else:
                assert original[key] == result[key], f"Field {key} doesn't match"
        else:
            # Check if there's a field mapping issue
            snake_key = camel_to_snake(key)
            if snake_key in result:
                # Handle sets vs lists for known set fields
                if key in ["failedReferenceTaskNames", "failedTaskNames"]:
                    if isinstance(original[key], list) and isinstance(
                        result[snake_key], (list, set)
                    ):
                        assert set(original[key]) == set(
                            result[snake_key]
                        ), f"Field {key} doesn't match after set conversion"
                    continue
                # Compare with the snake_case key
                if isinstance(original[key], dict) and isinstance(
                    result[snake_key], dict
                ):
                    compare_json_objects(original[key], result[snake_key])
                elif isinstance(original[key], list) and isinstance(
                    result[snake_key], list
                ):
                    assert len(original[key]) == len(result[snake_key])
                else:
                    assert (
                        original[key] == result[snake_key]
                    ), f"Field {key} doesn't match"
            else:
                # Check if the attribute is defined in swagger_types but has a different JSON name
                for py_field, json_field in WorkflowAdapter.attribute_map.items():
                    if json_field == key and py_field in result:
                        if key in ["failedReferenceTaskNames", "failedTaskNames"]:
                            if isinstance(original[key], list) and isinstance(
                                result[py_field], (list, set)
                            ):
                                assert set(original[key]) == set(
                                    result[py_field]
                                ), f"Field {key} doesn't match after set conversion"
                            break
                        if isinstance(original[key], dict) and isinstance(
                            result[py_field], dict
                        ):
                            compare_json_objects(original[key], result[py_field])
                        elif isinstance(original[key], list) and isinstance(
                            result[py_field], list
                        ):
                            assert len(original[key]) == len(result[py_field])
                        else:
                            assert (
                                original[key] == result[py_field]
                            ), f"Field {key} doesn't match"
                        break
                else:
                    # If the field isn't in result, and we can't find a mapping,
                    # it might be a field that isn't defined in the model
                    raise Exception(f"Field {key} is missing in the result")


def camel_to_snake(name):
    """Convert camelCase to snake_case"""

    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
