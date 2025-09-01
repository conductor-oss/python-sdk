import pytest

from conductor.client.http.models import Task, WorkflowRun


@pytest.fixture
def mock_task1(mocker):
    """Set up test fixture with mock task 1."""
    task = mocker.Mock(spec=Task)
    task.task_def_name = "test_task_1"
    task.status = "COMPLETED"
    task.workflow_task = mocker.Mock()
    task.workflow_task.task_reference_name = "task_ref_1"
    return task


@pytest.fixture
def mock_task2(mocker):
    """Set up test fixture with mock task 2."""
    task = mocker.Mock(spec=Task)
    task.task_def_name = "test_task_2"
    task.status = "IN_PROGRESS"
    task.workflow_task = mocker.Mock()
    task.workflow_task.task_reference_name = "task_ref_2"
    return task


@pytest.fixture
def valid_data(mock_task1, mock_task2):
    """Set up test fixture with valid test data."""
    return {
        "correlation_id": "test_correlation_123",
        "create_time": 1640995200000,
        "created_by": "test_user",
        "input": {"param1": "value1", "param2": 123},
        "output": {"result": "success"},
        "priority": 5,
        "request_id": "req_123",
        "status": "COMPLETED",
        "tasks": [mock_task1, mock_task2],
        "update_time": 1640995260000,
        "variables": {"var1": "value1"},
        "workflow_id": "workflow_123",
    }


def test_constructor_accepts_all_existing_parameters(valid_data):
    """Test that constructor accepts all documented parameters."""
    # Test with all parameters
    workflow_run = WorkflowRun(**valid_data)

    # Verify all parameters were set
    assert workflow_run.correlation_id == "test_correlation_123"
    assert workflow_run.create_time == 1640995200000
    assert workflow_run.created_by == "test_user"
    assert workflow_run.input == {"param1": "value1", "param2": 123}
    assert workflow_run.output == {"result": "success"}
    assert workflow_run.priority == 5
    assert workflow_run.request_id == "req_123"
    assert workflow_run.status == "COMPLETED"
    assert workflow_run.tasks == [valid_data["tasks"][0], valid_data["tasks"][1]]
    assert workflow_run.update_time == 1640995260000
    assert workflow_run.variables == {"var1": "value1"}
    assert workflow_run.workflow_id == "workflow_123"


def test_constructor_accepts_none_values():
    """Test that constructor handles None values for optional parameters."""
    workflow_run = WorkflowRun()

    # All fields should be None initially
    assert workflow_run.correlation_id is None
    assert workflow_run.create_time is None
    assert workflow_run.created_by is None
    assert workflow_run.input is None
    assert workflow_run.output is None
    assert workflow_run.priority is None
    assert workflow_run.request_id is None
    assert workflow_run.status is None
    assert workflow_run.tasks is None
    assert workflow_run.update_time is None
    assert workflow_run.variables is None
    assert workflow_run.workflow_id is None


def test_all_existing_properties_accessible(valid_data):
    """Test that all existing properties remain accessible."""
    workflow_run = WorkflowRun(**valid_data)

    # Test getter access
    properties_to_test = [
        "correlation_id",
        "create_time",
        "created_by",
        "input",
        "output",
        "priority",
        "request_id",
        "status",
        "tasks",
        "update_time",
        "variables",
        "workflow_id",
        "reason_for_incompletion",
    ]

    for prop in properties_to_test:
        # Should not raise AttributeError
        getattr(workflow_run, prop)
        assert hasattr(workflow_run, prop)


def test_all_existing_setters_functional(mock_task1):
    """Test that all existing property setters remain functional."""
    workflow_run = WorkflowRun()

    # Test setter access
    workflow_run.correlation_id = "new_correlation"
    workflow_run.create_time = 9999999
    workflow_run.created_by = "new_user"
    workflow_run.input = {"new": "input"}
    workflow_run.output = {"new": "output"}
    workflow_run.priority = 10
    workflow_run.request_id = "new_request"
    workflow_run.tasks = [mock_task1]
    workflow_run.update_time = 8888888
    workflow_run.variables = {"new": "variables"}
    workflow_run.workflow_id = "new_workflow"

    # Verify setters worked
    assert workflow_run.correlation_id == "new_correlation"
    assert workflow_run.create_time == 9999999
    assert workflow_run.created_by == "new_user"
    assert workflow_run.input == {"new": "input"}
    assert workflow_run.output == {"new": "output"}
    assert workflow_run.priority == 10
    assert workflow_run.request_id == "new_request"
    assert workflow_run.tasks == [mock_task1]
    assert workflow_run.update_time == 8888888
    assert workflow_run.variables == {"new": "variables"}
    assert workflow_run.workflow_id == "new_workflow"


def test_status_validation_rules_unchanged():
    """Test that status validation rules remain the same."""
    workflow_run = WorkflowRun()

    # Valid status values should work
    valid_statuses = [
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "TIMED_OUT",
        "TERMINATED",
        "PAUSED",
    ]
    for status in valid_statuses:
        workflow_run.status = status
        assert workflow_run.status == status

    # Invalid status should raise ValueError
    with pytest.raises(ValueError, match="Invalid value for `status`") as excinfo:
        workflow_run.status = "INVALID_STATUS"

    assert "INVALID_STATUS" in str(excinfo.value)


def test_field_types_unchanged(valid_data):
    """Test that field types haven't changed."""
    workflow_run = WorkflowRun(**valid_data)

    # String fields
    assert isinstance(workflow_run.correlation_id, str)
    assert isinstance(workflow_run.created_by, str)
    assert isinstance(workflow_run.request_id, str)
    assert isinstance(workflow_run.status, str)
    assert isinstance(workflow_run.workflow_id, str)

    # Integer fields
    assert isinstance(workflow_run.create_time, int)
    assert isinstance(workflow_run.priority, int)
    assert isinstance(workflow_run.update_time, int)

    # Dictionary fields
    assert isinstance(workflow_run.input, dict)
    assert isinstance(workflow_run.output, dict)
    assert isinstance(workflow_run.variables, dict)

    # List field
    assert isinstance(workflow_run.tasks, list)


def test_status_check_methods_unchanged():
    """Test that status checking methods remain functional and consistent."""
    workflow_run = WorkflowRun()

    # Test is_completed method for terminal statuses
    terminal_statuses = ["COMPLETED", "FAILED", "TIMED_OUT", "TERMINATED"]
    for status in terminal_statuses:
        workflow_run.status = status
        assert (
            workflow_run.is_completed()
        ), f"is_completed() should return True for status: {status}"

    # Test is_completed method for non-terminal statuses
    non_terminal_statuses = ["RUNNING", "PAUSED"]
    for status in non_terminal_statuses:
        workflow_run.status = status
        assert (
            not workflow_run.is_completed()
        ), f"is_completed() should return False for status: {status}"

    # Test is_successful method
    successful_statuses = ["PAUSED", "COMPLETED"]
    for status in successful_statuses:
        workflow_run.status = status
        assert (
            workflow_run.is_successful()
        ), f"is_successful() should return True for status: {status}"

    # Test is_running method
    running_statuses = ["RUNNING", "PAUSED"]
    for status in running_statuses:
        workflow_run.status = status
        assert (
            workflow_run.is_running()
        ), f"is_running() should return True for status: {status}"


def test_get_task_method_signature_unchanged(mock_task1, mock_task2):
    """Test that get_task method signature and behavior remain unchanged."""
    workflow_run = WorkflowRun(tasks=[mock_task1, mock_task2])

    # Test get_task by name
    task = workflow_run.get_task(name="test_task_1")
    assert task == mock_task1

    # Test get_task by task_reference_name
    task = workflow_run.get_task(task_reference_name="task_ref_2")
    assert task == mock_task2

    # Test error when both parameters provided
    with pytest.raises(
        Exception, match="ONLY one of name or task_reference_name MUST be provided"
    ):
        workflow_run.get_task(name="test", task_reference_name="test")

    # Test error when no parameters provided
    with pytest.raises(
        Exception, match="ONLY one of name or task_reference_name MUST be provided"
    ):
        workflow_run.get_task()


def test_current_task_property_unchanged(mocker):
    """Test that current_task property behavior remains unchanged."""
    # Create workflow with tasks in different states
    scheduled_task = mocker.Mock(spec=Task)
    scheduled_task.status = "SCHEDULED"

    in_progress_task = mocker.Mock(spec=Task)
    in_progress_task.status = "IN_PROGRESS"

    completed_task = mocker.Mock(spec=Task)
    completed_task.status = "COMPLETED"

    workflow_run = WorkflowRun(tasks=[completed_task, scheduled_task, in_progress_task])

    # Should return the in_progress_task (last one that matches criteria)
    current = workflow_run.current_task
    assert current == in_progress_task

    # Test with no current tasks
    workflow_run_no_current = WorkflowRun(tasks=[completed_task])
    assert workflow_run_no_current.current_task is None


def test_utility_methods_unchanged(valid_data):
    """Test that utility methods (to_dict, to_str, __repr__, __eq__, __ne__) remain functional."""
    workflow_run1 = WorkflowRun(**valid_data)
    workflow_run2 = WorkflowRun(**valid_data)

    # Test to_dict
    result_dict = workflow_run1.to_dict()
    assert isinstance(result_dict, dict)

    # Test to_str
    str_repr = workflow_run1.to_str()
    assert isinstance(str_repr, str)

    # Test __repr__
    repr_str = repr(workflow_run1)
    assert isinstance(repr_str, str)

    # Test __eq__
    assert workflow_run1 == workflow_run2

    # Test __ne__
    workflow_run2.correlation_id = "different"
    assert workflow_run1 != workflow_run2


def test_swagger_metadata_unchanged():
    """Test that swagger metadata attributes remain unchanged."""
    # Test that swagger_types exists and contains expected keys
    expected_swagger_keys = {
        "correlation_id",
        "create_time",
        "created_by",
        "input",
        "output",
        "priority",
        "request_id",
        "status",
        "tasks",
        "update_time",
        "variables",
        "workflow_id",
    }

    assert set(WorkflowRun.swagger_types.keys()) == expected_swagger_keys

    # Test that attribute_map exists and contains expected keys
    expected_attribute_keys = {
        "correlation_id",
        "create_time",
        "created_by",
        "input",
        "output",
        "priority",
        "request_id",
        "status",
        "tasks",
        "update_time",
        "variables",
        "workflow_id",
    }

    assert set(WorkflowRun.attribute_map.keys()) == expected_attribute_keys

    # Test specific type mappings
    assert WorkflowRun.swagger_types["correlation_id"] == "str"
    assert WorkflowRun.swagger_types["create_time"] == "int"
    assert WorkflowRun.swagger_types["input"] == "dict(str, object)"
    assert WorkflowRun.swagger_types["tasks"] == "list[Task]"


def test_reason_for_incompletion_parameter_handling():
    """Test that reason_for_incompletion parameter is handled correctly."""
    # Test with reason_for_incompletion parameter
    workflow_run = WorkflowRun(
        status="FAILED",
        reason_for_incompletion="Task timeout",
    )

    assert workflow_run.reason_for_incompletion == "Task timeout"
    assert workflow_run.status == "FAILED"
