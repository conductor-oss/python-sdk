import pytest

from conductor.client.adapters.models.task_summary_adapter import TaskSummaryAdapter


@pytest.fixture
def valid_data():
    """Set up test fixture with valid data."""
    return {
        "workflow_id": "wf_123",
        "workflow_type": "test_workflow",
        "correlation_id": "corr_456",
        "scheduled_time": "2024-01-01T10:00:00Z",
        "start_time": "2024-01-01T10:05:00Z",
        "update_time": "2024-01-01T10:10:00Z",
        "end_time": "2024-01-01T10:15:00Z",
        "status": "COMPLETED",
        "reason_for_incompletion": None,
        "execution_time": 600000,  # milliseconds
        "queue_wait_time": 300000,  # milliseconds
        "task_def_name": "test_task",
        "task_type": "SIMPLE",
        "input": '{"key": "value"}',
        "output": '{"result": "success"}',
        "task_id": "task_789",
        "external_input_payload_storage_path": "/path/to/input",
        "external_output_payload_storage_path": "/path/to/output",
        "workflow_priority": 5,
    }


def test_constructor_accepts_all_current_fields(valid_data):
    """Test that constructor accepts all current fields without error."""
    task_summary = TaskSummaryAdapter(**valid_data)

    # Verify all fields are set correctly
    assert task_summary.workflow_id == "wf_123"
    assert task_summary.workflow_type == "test_workflow"
    assert task_summary.correlation_id == "corr_456"
    assert task_summary.scheduled_time == "2024-01-01T10:00:00Z"
    assert task_summary.start_time == "2024-01-01T10:05:00Z"
    assert task_summary.update_time == "2024-01-01T10:10:00Z"
    assert task_summary.end_time == "2024-01-01T10:15:00Z"
    assert task_summary.status == "COMPLETED"
    assert task_summary.reason_for_incompletion is None
    assert task_summary.execution_time == 600000
    assert task_summary.queue_wait_time == 300000
    assert task_summary.task_def_name == "test_task"
    assert task_summary.task_type == "SIMPLE"
    assert task_summary.input == '{"key": "value"}'
    assert task_summary.output == '{"result": "success"}'
    assert task_summary.task_id == "task_789"
    assert task_summary.external_input_payload_storage_path == "/path/to/input"
    assert task_summary.external_output_payload_storage_path == "/path/to/output"
    assert task_summary.workflow_priority == 5


def test_constructor_with_no_arguments():
    """Test that constructor works with no arguments (all fields optional)."""
    task_summary = TaskSummaryAdapter()

    # All fields should be None initially
    assert task_summary.workflow_id is None
    assert task_summary.workflow_type is None
    assert task_summary.correlation_id is None
    assert task_summary.scheduled_time is None
    assert task_summary.start_time is None
    assert task_summary.update_time is None
    assert task_summary.end_time is None
    assert task_summary.status is None
    assert task_summary.reason_for_incompletion is None
    assert task_summary.execution_time is None
    assert task_summary.queue_wait_time is None
    assert task_summary.task_def_name is None
    assert task_summary.task_type is None
    assert task_summary.input is None
    assert task_summary.output is None
    assert task_summary.task_id is None
    assert task_summary.external_input_payload_storage_path is None
    assert task_summary.external_output_payload_storage_path is None
    assert task_summary.workflow_priority is None


def test_all_property_getters_exist(valid_data):
    """Test that all property getters exist and return correct types."""
    task_summary = TaskSummaryAdapter(**valid_data)

    # String properties
    assert isinstance(task_summary.workflow_id, str)
    assert isinstance(task_summary.workflow_type, str)
    assert isinstance(task_summary.correlation_id, str)
    assert isinstance(task_summary.scheduled_time, str)
    assert isinstance(task_summary.start_time, str)
    assert isinstance(task_summary.update_time, str)
    assert isinstance(task_summary.end_time, str)
    assert isinstance(task_summary.status, str)
    assert isinstance(task_summary.task_def_name, str)
    assert isinstance(task_summary.task_type, str)
    assert isinstance(task_summary.input, str)
    assert isinstance(task_summary.output, str)
    assert isinstance(task_summary.task_id, str)
    assert isinstance(task_summary.external_input_payload_storage_path, str)
    assert isinstance(task_summary.external_output_payload_storage_path, str)

    # Integer properties
    assert isinstance(task_summary.execution_time, int)
    assert isinstance(task_summary.queue_wait_time, int)
    assert isinstance(task_summary.workflow_priority, int)

    # Optional string property
    assert task_summary.reason_for_incompletion is None


def test_all_property_setters_exist():
    """Test that all property setters exist and work correctly."""
    task_summary = TaskSummaryAdapter()

    # Test string setters
    task_summary.workflow_id = "new_wf_id"
    assert task_summary.workflow_id == "new_wf_id"

    task_summary.workflow_type = "new_workflow_type"
    assert task_summary.workflow_type == "new_workflow_type"

    task_summary.correlation_id = "new_corr_id"
    assert task_summary.correlation_id == "new_corr_id"

    task_summary.scheduled_time = "2024-02-01T10:00:00Z"
    assert task_summary.scheduled_time == "2024-02-01T10:00:00Z"

    task_summary.start_time = "2024-02-01T10:05:00Z"
    assert task_summary.start_time == "2024-02-01T10:05:00Z"

    task_summary.update_time = "2024-02-01T10:10:00Z"
    assert task_summary.update_time == "2024-02-01T10:10:00Z"

    task_summary.end_time = "2024-02-01T10:15:00Z"
    assert task_summary.end_time == "2024-02-01T10:15:00Z"

    task_summary.reason_for_incompletion = "Test reason"
    assert task_summary.reason_for_incompletion == "Test reason"

    task_summary.task_def_name = "new_task_def"
    assert task_summary.task_def_name == "new_task_def"

    task_summary.task_type = "new_task_type"
    assert task_summary.task_type == "new_task_type"

    task_summary.input = '{"new": "input"}'
    assert task_summary.input == '{"new": "input"}'

    task_summary.output = '{"new": "output"}'
    assert task_summary.output == '{"new": "output"}'

    task_summary.task_id = "new_task_id"
    assert task_summary.task_id == "new_task_id"

    task_summary.external_input_payload_storage_path = "/new/input/path"
    assert task_summary.external_input_payload_storage_path == "/new/input/path"

    task_summary.external_output_payload_storage_path = "/new/output/path"
    assert task_summary.external_output_payload_storage_path == "/new/output/path"

    # Test integer setters
    task_summary.execution_time = 1000000
    assert task_summary.execution_time == 1000000

    task_summary.queue_wait_time = 500000
    assert task_summary.queue_wait_time == 500000

    task_summary.workflow_priority = 10
    assert task_summary.workflow_priority == 10


def test_status_enum_validation_all_allowed_values():
    """Test that status setter accepts all currently allowed enum values."""
    task_summary = TaskSummaryAdapter()

    allowed_statuses = [
        "IN_PROGRESS",
        "CANCELED",
        "FAILED",
        "FAILED_WITH_TERMINAL_ERROR",
        "COMPLETED",
        "COMPLETED_WITH_ERRORS",
        "SCHEDULED",
        "TIMED_OUT",
        "SKIPPED",
    ]

    for status in allowed_statuses:
        task_summary.status = status
        assert task_summary.status == status


def test_status_enum_validation_rejects_invalid_values():
    """Test that status setter rejects invalid enum values."""
    task_summary = TaskSummaryAdapter()

    invalid_statuses = [
        "INVALID_STATUS",
        "RUNNING",
        "PENDING",
        "ERROR",
        "",
        None,
    ]

    for invalid_status in invalid_statuses:
        with pytest.raises(ValueError, match="Invalid"):
            task_summary.status = invalid_status


def test_status_validation_in_constructor():
    """Test that status validation works in constructor."""
    # Valid status in constructor
    task_summary = TaskSummaryAdapter(status="COMPLETED")
    assert task_summary.status == "COMPLETED"

    # Invalid status in constructor should raise ValueError
    with pytest.raises(ValueError, match="Invalid"):
        TaskSummaryAdapter(status="INVALID_STATUS")


def test_swagger_types_contains_minimum_required_fields():
    """Test that swagger_types contains all minimum required fields and types."""
    # Define the minimum required fields that must exist for backward compatibility
    minimum_required_swagger_types = {
        "workflow_id": "str",
        "workflow_type": "str",
        "correlation_id": "str",
        "scheduled_time": "str",
        "start_time": "str",
        "update_time": "str",
        "end_time": "str",
        "status": "str",
        "reason_for_incompletion": "str",
        "execution_time": "int",
        "queue_wait_time": "int",
        "task_def_name": "str",
        "task_type": "str",
        "input": "str",
        "output": "str",
        "task_id": "str",
        "external_input_payload_storage_path": "str",
        "external_output_payload_storage_path": "str",
        "workflow_priority": "int",
    }

    # Check that all required fields exist with correct types
    for field, expected_type in minimum_required_swagger_types.items():
        assert (
            field in TaskSummaryAdapter.swagger_types
        ), f"Required field '{field}' missing from swagger_types"
        assert (
            TaskSummaryAdapter.swagger_types[field] == expected_type
        ), f"Field '{field}' has type '{TaskSummaryAdapter.swagger_types[field]}', expected '{expected_type}'"


def test_attribute_map_contains_minimum_required_mappings():
    """Test that attribute_map contains all minimum required mappings."""
    # Define the minimum required mappings that must exist for backward compatibility
    minimum_required_attribute_map = {
        "workflow_id": "workflowId",
        "workflow_type": "workflowType",
        "correlation_id": "correlationId",
        "scheduled_time": "scheduledTime",
        "start_time": "startTime",
        "update_time": "updateTime",
        "end_time": "endTime",
        "status": "status",
        "reason_for_incompletion": "reasonForIncompletion",
        "execution_time": "executionTime",
        "queue_wait_time": "queueWaitTime",
        "task_def_name": "taskDefName",
        "task_type": "taskType",
        "input": "input",
        "output": "output",
        "task_id": "taskId",
        "external_input_payload_storage_path": "externalInputPayloadStoragePath",
        "external_output_payload_storage_path": "externalOutputPayloadStoragePath",
        "workflow_priority": "workflowPriority",
    }

    # Check that all required mappings exist with correct values
    for field, expected_mapping in minimum_required_attribute_map.items():
        assert (
            field in TaskSummaryAdapter.attribute_map
        ), f"Required field '{field}' missing from attribute_map"
        assert (
            TaskSummaryAdapter.attribute_map[field] == expected_mapping
        ), f"Field '{field}' maps to '{TaskSummaryAdapter.attribute_map[field]}', expected '{expected_mapping}'"


def test_to_dict_method_exists_and_works(valid_data):
    """Test that to_dict method exists and returns expected structure."""
    task_summary = TaskSummaryAdapter(**valid_data)
    result_dict = task_summary.to_dict()

    assert isinstance(result_dict, dict)

    # Check that all minimum required fields are present in the dictionary
    minimum_required_fields = {
        "workflow_id",
        "workflow_type",
        "correlation_id",
        "scheduled_time",
        "start_time",
        "update_time",
        "end_time",
        "status",
        "reason_for_incompletion",
        "execution_time",
        "queue_wait_time",
        "task_def_name",
        "task_type",
        "input",
        "output",
        "task_id",
        "external_input_payload_storage_path",
        "external_output_payload_storage_path",
        "workflow_priority",
    }

    for field in minimum_required_fields:
        assert (
            field in result_dict
        ), f"Required field '{field}' missing from to_dict() output"


def test_to_str_method_exists(valid_data):
    """Test that to_str method exists."""
    task_summary = TaskSummaryAdapter(**valid_data)
    str_result = task_summary.to_str()
    assert isinstance(str_result, str)


def test_repr_method_exists(valid_data):
    """Test that __repr__ method exists."""
    task_summary = TaskSummaryAdapter(**valid_data)
    repr_result = repr(task_summary)
    assert isinstance(repr_result, str)


def test_equality_methods_exist(valid_data):
    """Test that __eq__ and __ne__ methods exist and work correctly."""
    task_summary1 = TaskSummaryAdapter(**valid_data)
    task_summary2 = TaskSummaryAdapter(**valid_data)
    task_summary3 = TaskSummaryAdapter(workflow_id="different_id")

    # Test equality
    assert task_summary1 == task_summary2
    assert task_summary1 != task_summary3

    # Test inequality
    assert not (task_summary1 != task_summary2)
    assert task_summary1 != task_summary3


def test_discriminator_attribute_exists():
    """Test that discriminator attribute exists and is None."""
    task_summary = TaskSummaryAdapter()
    assert task_summary.discriminator is None


def test_backward_compatibility_field_count():
    """Test that the model has at least the expected number of fields."""
    # This test ensures no fields are removed
    expected_minimum_field_count = 19
    actual_field_count = len(TaskSummaryAdapter.swagger_types)

    assert actual_field_count >= expected_minimum_field_count, (
        f"Model has {actual_field_count} fields, expected at least {expected_minimum_field_count}. "
        "Fields may have been removed, breaking backward compatibility."
    )


def test_backward_compatibility_status_enum_values():
    """Test that all expected status enum values are still supported."""
    # This test ensures no enum values are removed
    expected_minimum_status_values = {
        "IN_PROGRESS",
        "CANCELED",
        "FAILED",
        "FAILED_WITH_TERMINAL_ERROR",
        "COMPLETED",
        "COMPLETED_WITH_ERRORS",
        "SCHEDULED",
        "TIMED_OUT",
        "SKIPPED",
    }

    task_summary = TaskSummaryAdapter()

    # Test that all expected values are still accepted
    for status in expected_minimum_status_values:
        try:
            task_summary.status = status
            assert task_summary.status == status
        except ValueError:  # noqa: PERF203
            pytest.fail(
                f"Status value '{status}' is no longer supported, breaking backward compatibility"
            )


def test_new_fields_are_optional_and_backward_compatible(valid_data):
    """Test that any new fields added don't break existing functionality."""
    # Test that old code can still create instances without new fields
    task_summary = TaskSummaryAdapter(**valid_data)

    # Verify the object was created successfully
    assert task_summary is not None

    # Test that to_dict() works with the old data
    result_dict = task_summary.to_dict()
    assert isinstance(result_dict, dict)

    # Test that all original fields are still accessible
    for field_name in valid_data.keys():
        assert hasattr(
            task_summary, field_name
        ), f"Original field '{field_name}' is no longer accessible"
