import pytest

from conductor.client.http.models.task_result import TaskResult
from conductor.shared.http.enums.task_result_status import TaskResultStatus


@pytest.fixture
def valid_workflow_id():
    """Set up test fixture with valid workflow ID."""
    return "workflow_123"


@pytest.fixture
def valid_task_id():
    """Set up test fixture with valid task ID."""
    return "task_456"


@pytest.fixture
def valid_status_values():
    """Set up test fixture with valid status values from enum."""
    return [status.name for status in TaskResultStatus]


@pytest.fixture
def valid_status(valid_status_values):
    """Set up test fixture with a valid status value."""
    return valid_status_values[0] if valid_status_values else None


def test_required_fields_exist_and_accessible(valid_workflow_id, valid_task_id):
    """Test that required fields (workflow_instance_id, task_id) exist and are accessible."""
    task_result = TaskResult(
        workflow_instance_id=valid_workflow_id,
        task_id=valid_task_id,
    )

    # Test field accessibility
    assert task_result.workflow_instance_id == valid_workflow_id
    assert task_result.task_id == valid_task_id

    # Test private attributes exist
    assert hasattr(task_result, "_workflow_instance_id")
    assert hasattr(task_result, "_task_id")


def test_all_existing_fields_exist(valid_workflow_id, valid_task_id):
    """Test that all known fields from the original model still exist."""
    expected_fields = [
        "workflow_instance_id",
        "task_id",
        "reason_for_incompletion",
        "callback_after_seconds",
        "worker_id",
        "status",
        "output_data",
        "logs",
        "external_output_payload_storage_path",
        "sub_workflow_id",
    ]

    task_result = TaskResult(
        workflow_instance_id=valid_workflow_id,
        task_id=valid_task_id,
    )

    for field in expected_fields:
        assert hasattr(
            task_result, field
        ), f"Field '{field}' is missing from TaskResult"


def test_field_types_unchanged(valid_workflow_id, valid_task_id, valid_status):
    """Test that existing field types haven't changed."""
    expected_types = {
        "workflow_instance_id": str,
        "task_id": str,
        "reason_for_incompletion": str,
        "callback_after_seconds": int,
        "worker_id": str,
        "status": str,  # Note: stored as enum but accessed as string
        "output_data": dict,
        "logs": list,
        "external_output_payload_storage_path": str,
        "sub_workflow_id": str,
    }

    task_result = TaskResult(
        workflow_instance_id=valid_workflow_id,
        task_id=valid_task_id,
        reason_for_incompletion="test reason",
        callback_after_seconds=30,
        worker_id="worker_123",
        status=valid_status,
        output_data={"key": "value"},
        logs=[],
        external_output_payload_storage_path="/path/to/storage",
        sub_workflow_id="sub_workflow_789",
    )

    for field, expected_type in expected_types.items():
        value = getattr(task_result, field)
        if value is not None:  # Skip None values for optional fields
            if field == "status":
                # Status is stored as enum but we verify string access works
                assert isinstance(
                    value.name if hasattr(value, "name") else value, str
                ), f"Field '{field}' type changed from {expected_type}"
            else:
                assert isinstance(
                    value, expected_type
                ), f"Field '{field}' type changed from {expected_type}"


def test_swagger_types_structure_unchanged():
    """Test that swagger_types dictionary structure is preserved."""
    expected_swagger_types = {
        "workflow_instance_id": "str",
        "task_id": "str",
        "reason_for_incompletion": "str",
        "callback_after_seconds": "int",
        "worker_id": "str",
        "status": "str",
        "output_data": "dict(str, object)",
        "logs": "list[TaskExecLog]",
        "external_output_payload_storage_path": "str",
        "sub_workflow_id": "str",
    }

    for field, type_str in expected_swagger_types.items():
        assert (
            field in TaskResult.swagger_types
        ), f"Field '{field}' missing from swagger_types"
        assert (
            TaskResult.swagger_types[field] == type_str
        ), f"swagger_types for '{field}' changed"


def test_attribute_map_structure_unchanged():
    """Test that attribute_map dictionary structure is preserved."""
    expected_attribute_map = {
        "workflow_instance_id": "workflowInstanceId",
        "task_id": "taskId",
        "reason_for_incompletion": "reasonForIncompletion",
        "callback_after_seconds": "callbackAfterSeconds",
        "worker_id": "workerId",
        "status": "status",
        "output_data": "outputData",
        "logs": "logs",
        "external_output_payload_storage_path": "externalOutputPayloadStoragePath",
        "sub_workflow_id": "subWorkflowId",
    }

    for field, json_key in expected_attribute_map.items():
        assert (
            field in TaskResult.attribute_map
        ), f"Field '{field}' missing from attribute_map"
        assert (
            TaskResult.attribute_map[field] == json_key
        ), f"attribute_map for '{field}' changed"


def test_constructor_with_required_fields_only(valid_workflow_id, valid_task_id):
    """Test constructor works with only required fields."""
    task_result = TaskResult(
        workflow_instance_id=valid_workflow_id,
        task_id=valid_task_id,
    )

    assert task_result.workflow_instance_id == valid_workflow_id
    assert task_result.task_id == valid_task_id

    # Optional fields should be None
    assert task_result.reason_for_incompletion is None
    assert task_result.callback_after_seconds is None
    assert task_result.worker_id is None
    assert task_result.status is None
    assert task_result.output_data is None
    assert task_result.logs is None
    assert task_result.external_output_payload_storage_path is None
    assert task_result.sub_workflow_id is None


def test_constructor_with_all_fields(valid_workflow_id, valid_task_id, valid_status):
    """Test constructor works with all fields provided."""
    test_data = {
        "workflow_instance_id": valid_workflow_id,
        "task_id": valid_task_id,
        "reason_for_incompletion": "test reason",
        "callback_after_seconds": 30,
        "worker_id": "worker_123",
        "status": valid_status,
        "output_data": {"key": "value"},
        "logs": [],
        "external_output_payload_storage_path": "/path/to/storage",
        "sub_workflow_id": "sub_workflow_789",
    }

    task_result = TaskResult(**test_data)

    for field, expected_value in test_data.items():
        actual_value = getattr(task_result, field)

        assert actual_value == expected_value


def test_status_validation_unchanged(valid_workflow_id, valid_task_id, valid_status):
    """Test that status validation behavior is preserved."""
    task_result = TaskResult(
        workflow_instance_id=valid_workflow_id,
        task_id=valid_task_id,
    )

    # Test valid status assignment
    if valid_status:
        task_result.status = valid_status
        assert task_result.status == valid_status

    # Test invalid status assignment raises ValueError
    with pytest.raises(ValueError, match="Invalid value for `status`"):
        task_result.status = "INVALID_STATUS"


def test_property_setters_work(valid_workflow_id, valid_task_id):
    """Test that all property setters still function correctly."""
    task_result = TaskResult(
        workflow_instance_id=valid_workflow_id,
        task_id=valid_task_id,
    )

    # Test setting optional fields via properties
    task_result.reason_for_incompletion = "updated reason"
    task_result.callback_after_seconds = 60
    task_result.worker_id = "new_worker"
    task_result.output_data = {"new_key": "new_value"}
    task_result.logs = ["log1", "log2"]
    task_result.external_output_payload_storage_path = "/new/path"
    task_result.sub_workflow_id = "new_sub_workflow"

    # Verify assignments worked
    assert task_result.reason_for_incompletion == "updated reason"
    assert task_result.callback_after_seconds == 60
    assert task_result.worker_id == "new_worker"
    assert task_result.output_data == {"new_key": "new_value"}
    assert task_result.logs == ["log1", "log2"]
    assert task_result.external_output_payload_storage_path == "/new/path"
    assert task_result.sub_workflow_id == "new_sub_workflow"


def test_utility_methods_exist(valid_workflow_id, valid_task_id):
    """Test that utility methods still exist and work."""
    task_result = TaskResult(
        workflow_instance_id=valid_workflow_id,
        task_id=valid_task_id,
    )

    # Test to_dict method exists and returns dict
    result_dict = task_result.to_dict()
    assert isinstance(result_dict, dict)
    assert "workflow_instance_id" in result_dict
    assert "task_id" in result_dict

    # Test to_str method exists and returns string
    result_str = task_result.to_str()
    assert isinstance(result_str, str)

    # Test __repr__ method
    repr_str = repr(task_result)
    assert isinstance(repr_str, str)


def test_add_output_data_method_exists(valid_workflow_id, valid_task_id):
    """Test that the add_output_data convenience method still works."""
    task_result = TaskResult(
        workflow_instance_id=valid_workflow_id,
        task_id=valid_task_id,
    )

    # Test adding to None output_data
    task_result.add_output_data("key1", "value1")
    assert task_result.output_data == {"key1": "value1"}

    # Test adding to existing output_data
    task_result.add_output_data("key2", "value2")
    assert task_result.output_data == {"key1": "value1", "key2": "value2"}


def test_equality_methods_work(valid_workflow_id, valid_task_id):
    """Test that equality comparison methods still work."""
    task_result1 = TaskResult(
        workflow_instance_id=valid_workflow_id,
        task_id=valid_task_id,
    )

    task_result2 = TaskResult(
        workflow_instance_id=valid_workflow_id,
        task_id=valid_task_id,
    )

    task_result3 = TaskResult(
        workflow_instance_id="different_id",
        task_id=valid_task_id,
    )

    # Test equality
    assert task_result1 == task_result2
    assert task_result1 != task_result3

    # Test inequality
    assert not (task_result1 != task_result2)
    assert task_result1 != task_result3


def test_discriminator_attribute_exists(valid_workflow_id, valid_task_id):
    """Test that discriminator attribute is still present."""
    task_result = TaskResult(
        workflow_instance_id=valid_workflow_id,
        task_id=valid_task_id,
    )

    assert hasattr(task_result, "discriminator")
    assert task_result.discriminator is None
