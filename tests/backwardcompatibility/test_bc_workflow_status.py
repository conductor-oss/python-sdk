import pytest

from conductor.client.adapters.models.workflow_status_adapter import WorkflowStatusAdapter


@pytest.fixture
def valid_workflow_id():
    """Set up test fixture with valid workflow ID."""
    return "test_workflow_123"


@pytest.fixture
def valid_correlation_id():
    """Set up test fixture with valid correlation ID."""
    return "corr_123"


@pytest.fixture
def valid_output():
    """Set up test fixture with valid output."""
    return {"result": "success", "data": {"key": "value"}}


@pytest.fixture
def valid_variables():
    """Set up test fixture with valid variables."""
    return {"var1": "value1", "var2": 42}


@pytest.fixture
def valid_status_values():
    """Set up test fixture with valid status values."""
    return ["RUNNING", "COMPLETED", "FAILED", "TIMED_OUT", "TERMINATED", "PAUSED"]


def test_constructor_exists_and_accepts_expected_parameters(
    valid_workflow_id, valid_correlation_id, valid_output, valid_variables
):
    """Test that constructor exists and accepts all expected parameters"""
    # Should work with no parameters (all optional)
    workflow_status = WorkflowStatusAdapter()
    assert isinstance(workflow_status, WorkflowStatusAdapter)

    # Should work with all parameters
    workflow_status = WorkflowStatusAdapter(
        workflow_id=valid_workflow_id,
        correlation_id=valid_correlation_id,
        output=valid_output,
        variables=valid_variables,
        status="RUNNING",
    )
    assert isinstance(workflow_status, WorkflowStatusAdapter)


def test_all_expected_fields_exist():
    """Test that all expected fields exist and are accessible"""
    workflow_status = WorkflowStatusAdapter()

    # Test that all expected properties exist
    expected_properties = [
        "workflow_id",
        "correlation_id",
        "output",
        "variables",
        "status",
    ]

    for prop in expected_properties:
        assert hasattr(workflow_status, prop), f"Property '{prop}' should exist"
        # Should be able to get the property
        getattr(workflow_status, prop)


def test_field_getters_and_setters_work(
    valid_workflow_id, valid_correlation_id, valid_output, valid_variables
):
    """Test that field getters and setters work as expected"""
    workflow_status = WorkflowStatusAdapter()

    # Test workflow_id
    workflow_status.workflow_id = valid_workflow_id
    assert workflow_status.workflow_id == valid_workflow_id

    # Test correlation_id
    workflow_status.correlation_id = valid_correlation_id
    assert workflow_status.correlation_id == valid_correlation_id

    # Test output
    workflow_status.output = valid_output
    assert workflow_status.output == valid_output

    # Test variables
    workflow_status.variables = valid_variables
    assert workflow_status.variables == valid_variables

    # Test status with valid value
    workflow_status.status = "RUNNING"
    assert workflow_status.status == "RUNNING"


def test_status_validation_rules_preserved(valid_status_values):
    """Test that status field validation rules are preserved"""
    workflow_status = WorkflowStatusAdapter()

    # Test that all historically valid status values still work
    for status_value in valid_status_values:
        workflow_status.status = status_value
        assert workflow_status.status == status_value

    # Test that invalid status still raises ValueError
    with pytest.raises(ValueError, match="Invalid value for `status`") as excinfo:
        workflow_status.status = "INVALID_STATUS"

    error_message = str(excinfo.value)
    assert "INVALID_STATUS" in error_message


def test_constructor_with_status_validation(valid_status_values):
    """Test that constructor properly validates status when provided"""
    # Valid status should work
    for status_value in valid_status_values:
        workflow_status = WorkflowStatusAdapter(status=status_value)
        assert workflow_status.status == status_value

    # Invalid status should raise ValueError
    with pytest.raises(ValueError, match="Invalid"):
        WorkflowStatusAdapter(status="INVALID_STATUS")


def test_none_values_allowed_for_applicable_fields():
    """Test that None values are allowed for fields that support them"""
    workflow_status = WorkflowStatusAdapter()

    # All fields should default to None
    assert workflow_status.workflow_id is None
    assert workflow_status.correlation_id is None
    assert workflow_status.output is None
    assert workflow_status.variables is None
    assert workflow_status.status is None

    # Should be able to explicitly set to None for fields that support it
    workflow_status.workflow_id = None
    workflow_status.correlation_id = None
    workflow_status.output = None
    workflow_status.variables = None

    # Status field does NOT allow None after construction due to validation
    with pytest.raises(ValueError, match="Invalid"):
        workflow_status.status = None


def test_expected_methods_exist(valid_workflow_id):
    """Test that expected methods exist and work"""
    workflow_status = WorkflowStatusAdapter(workflow_id=valid_workflow_id, status="COMPLETED")

    # Test methods exist
    expected_methods = [
        "to_dict",
        "to_str",
        "is_completed",
        "is_successful",
        "is_running",
    ]
    for method_name in expected_methods:
        assert hasattr(
            workflow_status, method_name
        ), f"Method '{method_name}' should exist"
        assert callable(
            getattr(workflow_status, method_name)
        ), f"Method '{method_name}' should be callable"


def test_is_completed_method_behavior():
    """Test that is_completed method works with expected status values"""
    workflow_status = WorkflowStatusAdapter()

    # Test terminal statuses
    terminal_statuses = ["COMPLETED", "FAILED", "TIMED_OUT", "TERMINATED"]
    for status in terminal_statuses:
        workflow_status.status = status
        assert (
            workflow_status.is_completed()
        ), f"Status '{status}' should be considered completed"

    # Test non-terminal statuses
    non_terminal_statuses = ["RUNNING", "PAUSED"]
    for status in non_terminal_statuses:
        workflow_status.status = status
        assert (
            not workflow_status.is_completed()
        ), f"Status '{status}' should not be considered completed"


def test_is_successful_method_behavior():
    """Test that is_successful method works with expected status values"""
    workflow_status = WorkflowStatusAdapter()

    # Test successful statuses
    successful_statuses = ["PAUSED", "COMPLETED"]
    for status in successful_statuses:
        workflow_status.status = status
        assert (
            workflow_status.is_successful()
        ), f"Status '{status}' should be considered successful"

    # Test non-successful statuses
    non_successful_statuses = ["RUNNING", "FAILED", "TIMED_OUT", "TERMINATED"]
    for status in non_successful_statuses:
        workflow_status.status = status
        assert (
            not workflow_status.is_successful()
        ), f"Status '{status}' should not be considered successful"


def test_is_running_method_behavior():
    """Test that is_running method works with expected status values"""
    workflow_status = WorkflowStatusAdapter()

    # Test running statuses
    running_statuses = ["RUNNING", "PAUSED"]
    for status in running_statuses:
        workflow_status.status = status
        assert (
            workflow_status.is_running()
        ), f"Status '{status}' should be considered running"

    # Test non-running statuses
    non_running_statuses = ["COMPLETED", "FAILED", "TIMED_OUT", "TERMINATED"]
    for status in non_running_statuses:
        workflow_status.status = status
        assert (
            not workflow_status.is_running()
        ), f"Status '{status}' should not be considered running"


def test_to_dict_method_returns_expected_structure(
    valid_workflow_id, valid_correlation_id, valid_output, valid_variables
):
    """Test that to_dict method returns expected structure"""
    workflow_status = WorkflowStatusAdapter(
        workflow_id=valid_workflow_id,
        correlation_id=valid_correlation_id,
        output=valid_output,
        variables=valid_variables,
        status="RUNNING",
    )

    result_dict = workflow_status.to_dict()

    # Should return a dictionary
    assert isinstance(result_dict, dict)

    # Should contain expected keys
    expected_keys = ["workflow_id", "correlation_id", "output", "variables", "status"]
    for key in expected_keys:
        assert key in result_dict, f"Key '{key}' should be in to_dict() result"


def test_string_representations_work(valid_workflow_id):
    """Test that string representation methods work"""
    workflow_status = WorkflowStatusAdapter(workflow_id=valid_workflow_id)

    # to_str should return a string
    str_repr = workflow_status.to_str()
    assert isinstance(str_repr, str)

    # __repr__ should return a string
    repr_result = repr(workflow_status)
    assert isinstance(repr_result, str)


def test_equality_methods_work(valid_workflow_id):
    """Test that equality methods work as expected"""
    workflow_status1 = WorkflowStatusAdapter(workflow_id=valid_workflow_id, status="RUNNING")
    workflow_status2 = WorkflowStatusAdapter(workflow_id=valid_workflow_id, status="RUNNING")
    workflow_status3 = WorkflowStatusAdapter(workflow_id="different_id", status="RUNNING")

    # Equal objects should be equal
    assert workflow_status1 == workflow_status2
    assert not (workflow_status1 != workflow_status2)

    # Different objects should not be equal
    assert workflow_status1 != workflow_status3
    assert workflow_status1 != workflow_status3


def test_attribute_map_preserved():
    """Test that attribute_map is preserved for API compatibility"""
    expected_attribute_map = {
        "workflow_id": "workflowId",
        "correlation_id": "correlationId",
        "output": "output",
        "variables": "variables",
        "status": "status",
    }

    assert hasattr(WorkflowStatusAdapter, "attribute_map")
    assert WorkflowStatusAdapter.attribute_map == expected_attribute_map


def test_swagger_types_preserved():
    """Test that swagger_types is preserved for API compatibility"""
    expected_swagger_types = {
        "workflow_id": "str",
        "correlation_id": "str",
        "output": "dict(str, object)",
        "variables": "dict(str, object)",
        "status": "str",
    }

    assert hasattr(WorkflowStatusAdapter, "swagger_types")
    assert WorkflowStatusAdapter.swagger_types == expected_swagger_types
