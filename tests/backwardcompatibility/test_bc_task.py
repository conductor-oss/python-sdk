import pytest

from conductor.client.http.models import Task, TaskResult, WorkflowTask
from conductor.client.http.models.task_result_status import TaskResultStatus


@pytest.fixture
def valid_task_data():
    """Set up test fixture with valid data for existing fields."""
    return {
        "task_type": "TEST_TASK",
        "status": "IN_PROGRESS",
        "input_data": {"key": "value"},
        "reference_task_name": "ref_task",
        "retry_count": 3,
        "seq": 1,
        "correlation_id": "corr_123",
        "poll_count": 5,
        "task_def_name": "task_def",
        "scheduled_time": 1640995200000,
        "start_time": 1640995200000,
        "end_time": 1640995300000,
        "update_time": 1640995250000,
        "start_delay_in_seconds": 10,
        "retried_task_id": "retry_123",
        "retried": False,
        "executed": True,
        "callback_from_worker": False,
        "response_timeout_seconds": 30,
        "workflow_instance_id": "workflow_123",
        "workflow_type": "TEST_WORKFLOW",
        "task_id": "task_123",
        "reason_for_incompletion": "timeout",
        "callback_after_seconds": 60,
        "worker_id": "worker_123",
        "output_data": {"result": "success"},
        "domain": "test_domain",
        "rate_limit_per_frequency": 100,
        "rate_limit_frequency_in_seconds": 60,
        "external_input_payload_storage_path": "/input/path",
        "external_output_payload_storage_path": "/output/path",
        "workflow_priority": 5,
        "execution_name_space": "test_namespace",
        "isolation_group_id": "group_123",
        "iteration": 2,
        "sub_workflow_id": "sub_123",
        "subworkflow_changed": False,
        "loop_over_task": True,
        "queue_wait_time": 1000,
    }


def test_constructor_accepts_all_existing_parameters(valid_task_data):
    """Test that constructor accepts all existing parameters without error."""
    # Test constructor with all parameters
    task = Task(**valid_task_data)

    # Verify task was created successfully
    assert isinstance(task, Task)

    # Test constructor with no parameters (should work)
    empty_task = Task()
    assert isinstance(empty_task, Task)


def test_all_existing_properties_exist_and_accessible(valid_task_data):
    """Test that all existing properties exist and are accessible."""
    task = Task(**valid_task_data)

    # Test all string properties
    string_properties = [
        "task_type",
        "status",
        "reference_task_name",
        "correlation_id",
        "task_def_name",
        "retried_task_id",
        "workflow_instance_id",
        "workflow_type",
        "task_id",
        "reason_for_incompletion",
        "worker_id",
        "domain",
        "external_input_payload_storage_path",
        "external_output_payload_storage_path",
        "execution_name_space",
        "isolation_group_id",
        "sub_workflow_id",
    ]

    for prop in string_properties:
        assert hasattr(task, prop), f"Property {prop} should exist"
        value = getattr(task, prop)
        assert isinstance(value, str), f"Property {prop} should be string"

    # Test all integer properties
    int_properties = [
        "retry_count",
        "seq",
        "poll_count",
        "scheduled_time",
        "start_time",
        "end_time",
        "update_time",
        "start_delay_in_seconds",
        "response_timeout_seconds",
        "callback_after_seconds",
        "rate_limit_per_frequency",
        "rate_limit_frequency_in_seconds",
        "workflow_priority",
        "iteration",
        "queue_wait_time",
    ]

    for prop in int_properties:
        assert hasattr(task, prop), f"Property {prop} should exist"
        value = getattr(task, prop)
        assert isinstance(value, int), f"Property {prop} should be integer"

    # Test all boolean properties
    bool_properties = [
        "retried",
        "executed",
        "callback_from_worker",
        "subworkflow_changed",
        "loop_over_task",
    ]

    for prop in bool_properties:
        assert hasattr(task, prop), f"Property {prop} should exist"
        value = getattr(task, prop)
        assert isinstance(value, bool), f"Property {prop} should be boolean"

    # Test dict properties
    dict_properties = ["input_data", "output_data"]
    for prop in dict_properties:
        assert hasattr(task, prop), f"Property {prop} should exist"
        value = getattr(task, prop)
        assert isinstance(value, dict), f"Property {prop} should be dict"


def test_all_existing_setters_work(valid_task_data):
    """Test that all existing property setters work correctly."""
    task = Task()

    # Test setting each property individually
    for key, value in valid_task_data.items():
        if key == "workflow_task":  # Skip complex object for now
            continue
        setattr(task, key, value)
        assert getattr(task, key) == value, f"Setting {key} should work"


def test_status_validation_unchanged():
    """Test that status validation rules remain unchanged."""
    task = Task()

    # Valid status values should work
    valid_statuses = [
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

    for status in valid_statuses:
        task.status = status
        assert task.status == status, f"Valid status {status} should be accepted"

    # Invalid status should raise ValueError
    with pytest.raises(ValueError, match="Invalid"):
        task.status = "INVALID_STATUS"


def test_workflow_task_property_exists(mocker):
    """Test that workflow_task property exists and has correct type."""
    task = Task()

    # Should have workflow_task property
    assert hasattr(task, "workflow_task")

    # Should accept WorkflowTask objects
    mock_workflow_task = mocker.MagicMock(spec=WorkflowTask)
    task.workflow_task = mock_workflow_task
    assert task.workflow_task == mock_workflow_task


def test_task_definition_property_exists(mocker):
    """Test that task_definition property exists."""
    task = Task()

    # Should have task_definition property
    assert hasattr(task, "task_definition")

    # Should be settable (type checking may be loose)
    mock_task_def = mocker.MagicMock()
    task.task_definition = mock_task_def
    assert task.task_definition == mock_task_def


def test_to_dict_method_exists_and_works(valid_task_data):
    """Test that to_dict method exists and returns expected structure."""
    task = Task(**valid_task_data)

    # Method should exist
    assert hasattr(task, "to_dict")
    assert callable(getattr(task, "to_dict"))

    # Should return dict
    result = task.to_dict()
    assert isinstance(result, dict)

    # Should contain expected keys
    for key in valid_task_data.keys():
        assert key in result, f"to_dict should contain {key}"


def test_to_str_method_exists_and_works(valid_task_data):
    """Test that to_str method exists and returns string."""
    task = Task(**valid_task_data)

    # Method should exist
    assert hasattr(task, "to_str")
    assert callable(getattr(task, "to_str"))

    # Should return string
    result = task.to_str()
    assert isinstance(result, str)


def test_repr_method_exists_and_works(valid_task_data):
    """Test that __repr__ method exists and returns string."""
    task = Task(**valid_task_data)

    # Method should exist and work
    result = repr(task)
    assert isinstance(result, str)


def test_equality_methods_exist_and_work(valid_task_data):
    """Test that __eq__ and __ne__ methods exist and work."""
    task1 = Task(**valid_task_data)
    task2 = Task(**valid_task_data)
    task3 = Task(task_type="DIFFERENT")

    # Equal tasks should be equal
    assert task1 == task2
    assert not (task1 != task2)

    # Different tasks should not be equal
    assert task1 != task3
    assert task1 != task3

    # Should handle comparison with non-Task objects
    assert task1 != "not a task"
    assert task1 != "not a task"


def test_to_task_result_method_exists_and_works():
    """Test that to_task_result method exists and works correctly."""
    task_data = {
        "task_id": "test_123",
        "workflow_instance_id": "workflow_123",
        "worker_id": "worker_123",
    }
    task = Task(**task_data)

    # Method should exist
    assert hasattr(task, "to_task_result")
    assert callable(getattr(task, "to_task_result"))

    # Should work with default status
    result = task.to_task_result()
    assert isinstance(result, TaskResult)
    assert result.task_id == "test_123"
    assert result.workflow_instance_id == "workflow_123"
    assert result.worker_id == "worker_123"
    assert result.status == TaskResultStatus.COMPLETED

    # Should work with custom status
    result = task.to_task_result(TaskResultStatus.FAILED)
    assert result.status == TaskResultStatus.FAILED


def test_swagger_types_attribute_exists():
    """Test that swagger_types class attribute exists and has expected structure."""
    assert hasattr(Task, "swagger_types")
    assert isinstance(Task.swagger_types, dict)

    # Check for some key attributes
    expected_types = {
        "task_type": "str",
        "status": "str",
        "input_data": "dict(str, object)",
        "retry_count": "int",
        "retried": "bool",
        "workflow_task": "WorkflowTask",
    }

    for key, expected_type in expected_types.items():
        assert key in Task.swagger_types, f"swagger_types should contain {key}"
        assert (
            Task.swagger_types[key] == expected_type
        ), f"swagger_types[{key}] should be {expected_type}"


def test_attribute_map_exists():
    """Test that attribute_map class attribute exists and has expected structure."""
    assert hasattr(Task, "attribute_map")
    assert isinstance(Task.attribute_map, dict)

    # Check for some key mappings
    expected_mappings = {
        "task_type": "taskType",
        "input_data": "inputData",
        "reference_task_name": "referenceTaskName",
        "retry_count": "retryCount",
        "workflow_instance_id": "workflowInstanceId",
    }

    for key, expected_json_key in expected_mappings.items():
        assert key in Task.attribute_map, f"attribute_map should contain {key}"
        assert (
            Task.attribute_map[key] == expected_json_key
        ), f"attribute_map[{key}] should be {expected_json_key}"


def test_private_attributes_initialized():
    """Test that all private attributes are properly initialized."""
    task = Task()

    # All properties should have corresponding private attributes
    for attr_name in Task.swagger_types.keys():
        private_attr = f"_{attr_name}"
        assert hasattr(
            task, private_attr
        ), f"Private attribute {private_attr} should exist"


def test_discriminator_attribute_exists():
    """Test that discriminator attribute exists."""
    task = Task()
    assert hasattr(task, "discriminator")
    assert task.discriminator is None


def test_backward_compatibility_with_none_values():
    """Test that setting None values works for optional fields."""
    task = Task()

    # All fields should accept None (since they're optional in constructor)
    for attr_name in Task.swagger_types.keys():
        if attr_name != "status":  # Status has validation
            setattr(task, attr_name, None)
            assert (
                getattr(task, attr_name) is None
            ), f"Setting {attr_name} to None should work"
