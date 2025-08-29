import pytest

from conductor.client.http.models.rerun_workflow_request import RerunWorkflowRequest


@pytest.fixture
def valid_workflow_input():
    """Set up test fixture with valid workflow input data."""
    return {"param1": "value1", "param2": 123}


@pytest.fixture
def valid_task_input():
    """Set up test fixture with valid task input data."""
    return {"task_param": "task_value", "num_param": 456}


def test_class_exists():
    """Test that the RerunWorkflowRequest class still exists."""
    assert hasattr(RerunWorkflowRequest, "__init__")
    assert callable(RerunWorkflowRequest)


def test_required_attributes_exist():
    """Test that all expected class attributes exist."""
    # Check swagger_types mapping exists and contains expected fields
    assert hasattr(RerunWorkflowRequest, "swagger_types")
    expected_swagger_types = {
        "re_run_from_workflow_id": "str",
        "workflow_input": "dict(str, object)",
        "re_run_from_task_id": "str",
        "task_input": "dict(str, object)",
        "correlation_id": "str",
    }

    for field, expected_type in expected_swagger_types.items():
        assert field in RerunWorkflowRequest.swagger_types
        assert RerunWorkflowRequest.swagger_types[field] == expected_type

    # Check attribute_map exists and contains expected mappings
    assert hasattr(RerunWorkflowRequest, "attribute_map")
    expected_attribute_map = {
        "re_run_from_workflow_id": "reRunFromWorkflowId",
        "workflow_input": "workflowInput",
        "re_run_from_task_id": "reRunFromTaskId",
        "task_input": "taskInput",
        "correlation_id": "correlationId",
    }

    for field, expected_json_key in expected_attribute_map.items():
        assert field in RerunWorkflowRequest.attribute_map
        assert RerunWorkflowRequest.attribute_map[field] == expected_json_key


def test_constructor_with_no_parameters():
    """Test that constructor works with no parameters (all optional)."""
    request = RerunWorkflowRequest()

    # All fields should be None initially
    assert request.re_run_from_workflow_id is None
    assert request.workflow_input is None
    assert request.re_run_from_task_id is None
    assert request.task_input is None
    assert request.correlation_id is None


def test_constructor_with_all_parameters(valid_workflow_input, valid_task_input):
    """Test constructor with all parameters provided."""
    request = RerunWorkflowRequest(
        re_run_from_workflow_id="workflow_123",
        workflow_input=valid_workflow_input,
        re_run_from_task_id="task_456",
        task_input=valid_task_input,
        correlation_id="corr_789",
    )

    assert request.re_run_from_workflow_id == "workflow_123"
    assert request.workflow_input == valid_workflow_input
    assert request.re_run_from_task_id == "task_456"
    assert request.task_input == valid_task_input
    assert request.correlation_id == "corr_789"


def test_constructor_with_partial_parameters(valid_task_input):
    """Test constructor with only some parameters provided."""
    request = RerunWorkflowRequest(
        re_run_from_workflow_id="workflow_123", task_input=valid_task_input
    )

    assert request.re_run_from_workflow_id == "workflow_123"
    assert request.workflow_input is None
    assert request.re_run_from_task_id is None
    assert request.task_input == valid_task_input
    assert request.correlation_id is None


def test_property_getters_exist():
    """Test that all property getters still exist and work."""
    request = RerunWorkflowRequest()

    # Test that all getters exist and return None initially
    assert request.re_run_from_workflow_id is None
    assert request.workflow_input is None
    assert request.re_run_from_task_id is None
    assert request.task_input is None
    assert request.correlation_id is None


def test_property_setters_exist_and_work(valid_workflow_input, valid_task_input):
    """Test that all property setters exist and work correctly."""
    request = RerunWorkflowRequest()

    # Test re_run_from_workflow_id setter
    request.re_run_from_workflow_id = "workflow_123"
    assert request.re_run_from_workflow_id == "workflow_123"

    # Test workflow_input setter
    request.workflow_input = valid_workflow_input
    assert request.workflow_input == valid_workflow_input

    # Test re_run_from_task_id setter
    request.re_run_from_task_id = "task_456"
    assert request.re_run_from_task_id == "task_456"

    # Test task_input setter
    request.task_input = valid_task_input
    assert request.task_input == valid_task_input

    # Test correlation_id setter
    request.correlation_id = "corr_789"
    assert request.correlation_id == "corr_789"


def test_setters_accept_none_values():
    """Test that setters accept None values (no required field validation)."""
    request = RerunWorkflowRequest(
        re_run_from_workflow_id="test",
        workflow_input={"key": "value"},
        re_run_from_task_id="task_test",
        task_input={"task_key": "task_value"},
        correlation_id="correlation_test",
    )

    # All setters should accept None without raising errors
    request.re_run_from_workflow_id = None
    request.workflow_input = None
    request.re_run_from_task_id = None
    request.task_input = None
    request.correlation_id = None

    assert request.re_run_from_workflow_id is None
    assert request.workflow_input is None
    assert request.re_run_from_task_id is None
    assert request.task_input is None
    assert request.correlation_id is None


def test_string_fields_accept_string_values():
    """Test that string fields accept string values."""
    request = RerunWorkflowRequest()

    # Test string fields with various string values
    request.re_run_from_workflow_id = "workflow_id_123"
    request.re_run_from_task_id = "task_id_456"
    request.correlation_id = "correlation_id_789"

    assert request.re_run_from_workflow_id == "workflow_id_123"
    assert request.re_run_from_task_id == "task_id_456"
    assert request.correlation_id == "correlation_id_789"


def test_dict_fields_accept_dict_values():
    """Test that dict fields accept dictionary values."""
    request = RerunWorkflowRequest()

    # Test workflow_input with various dict structures
    workflow_input1 = {"simple": "value"}
    workflow_input2 = {"complex": {"nested": {"data": [1, 2, 3]}}}

    request.workflow_input = workflow_input1
    assert request.workflow_input == workflow_input1

    request.workflow_input = workflow_input2
    assert request.workflow_input == workflow_input2

    # Test task_input with various dict structures
    task_input1 = {"task_param": "value"}
    task_input2 = {"multiple": "params", "with": {"nested": "objects"}}

    request.task_input = task_input1
    assert request.task_input == task_input1

    request.task_input = task_input2
    assert request.task_input == task_input2


def test_core_methods_exist():
    """Test that core methods still exist and work."""
    request = RerunWorkflowRequest(
        re_run_from_workflow_id="test_id", workflow_input={"test": "data"}
    )

    # Test to_dict method exists and works
    assert hasattr(request, "to_dict")
    assert callable(request.to_dict)
    result_dict = request.to_dict()
    assert isinstance(result_dict, dict)

    # Test to_str method exists and works
    assert hasattr(request, "to_str")
    assert callable(request.to_str)
    result_str = request.to_str()
    assert isinstance(result_str, str)

    # Test __repr__ method works
    repr_result = repr(request)
    assert isinstance(repr_result, str)

    # Test __eq__ method exists and works
    request2 = RerunWorkflowRequest(
        re_run_from_workflow_id="test_id", workflow_input={"test": "data"}
    )
    assert request == request2

    # Test __ne__ method exists and works
    request3 = RerunWorkflowRequest(re_run_from_workflow_id="different_id")
    assert request != request3


def test_no_unexpected_validation_errors():
    """Test that no unexpected validation has been added."""
    # This test ensures that the current permissive behavior is maintained
    # The model should accept any values without type validation

    request = RerunWorkflowRequest()

    # These should not raise any validation errors based on current implementation
    # (though they might not be the intended types, the current model allows them)
    request.re_run_from_workflow_id = "valid_string"
    request.workflow_input = {"valid": "dict"}
    request.re_run_from_task_id = "valid_task_id"
    request.task_input = {"valid": "task_dict"}
    request.correlation_id = "valid_correlation"


def test_discriminator_attribute_exists():
    """Test that discriminator attribute exists and is set to None."""
    request = RerunWorkflowRequest()
    assert hasattr(request, "discriminator")
    assert request.discriminator is None
