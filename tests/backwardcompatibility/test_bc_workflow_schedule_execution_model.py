import pytest

from conductor.client.http.models import WorkflowScheduleExecutionModel


@pytest.fixture
def valid_data():
    """Set up test fixture with valid data."""
    return {
        "execution_id": "exec_123",
        "schedule_name": "daily_schedule",
        "scheduled_time": 1640995200,  # timestamp
        "execution_time": 1640995260,  # timestamp
        "workflow_name": "test_workflow",
        "workflow_id": "wf_456",
        "reason": "scheduled execution",
        "stack_trace": "stack trace info",
        "start_workflow_request": None,  # StartWorkflowRequest object
        "state": "EXECUTED",
    }


def test_constructor_with_all_none_parameters():
    """Test that constructor accepts all None values (current behavior)."""
    model = WorkflowScheduleExecutionModel()

    # Verify all fields are None initially
    assert model.execution_id is None
    assert model.schedule_name is None
    assert model.scheduled_time is None
    assert model.execution_time is None
    assert model.workflow_name is None
    assert model.workflow_id is None
    assert model.reason is None
    assert model.stack_trace is None
    assert model.start_workflow_request is None
    assert model.state is None


def test_constructor_with_valid_parameters(valid_data):
    """Test constructor with all valid parameters."""
    model = WorkflowScheduleExecutionModel(**valid_data)

    # Verify all fields are set correctly
    assert model.execution_id == "exec_123"
    assert model.schedule_name == "daily_schedule"
    assert model.scheduled_time == 1640995200
    assert model.execution_time == 1640995260
    assert model.workflow_name == "test_workflow"
    assert model.workflow_id == "wf_456"
    assert model.reason == "scheduled execution"
    assert model.stack_trace == "stack trace info"
    assert model.start_workflow_request is None
    assert model.state == "EXECUTED"


def test_all_expected_fields_exist():
    """Verify all expected fields still exist and are accessible."""
    model = WorkflowScheduleExecutionModel()

    expected_fields = [
        "execution_id",
        "schedule_name",
        "scheduled_time",
        "execution_time",
        "workflow_name",
        "workflow_id",
        "reason",
        "stack_trace",
        "start_workflow_request",
        "state",
    ]

    for field in expected_fields:
        # Test getter exists
        assert hasattr(model, field), f"Field '{field}' missing"
        # Test getter is callable
        getattr(model, field)
        # Test setter exists (property should allow assignment)
        if field == "state":
            # state field has validation, use valid value
            setattr(model, field, "POLLED")
        else:
            setattr(model, field, None)


def test_field_type_consistency():
    """Verify field types haven't changed."""
    model = WorkflowScheduleExecutionModel()

    # Test string fields (excluding state which has enum validation)
    string_fields = [
        "execution_id",
        "schedule_name",
        "workflow_name",
        "workflow_id",
        "reason",
        "stack_trace",
    ]

    for field in string_fields:
        setattr(model, field, "test_string")
        assert getattr(model, field) == "test_string"

    # Test state field with valid enum value
    setattr(model, "state", "POLLED")
    assert getattr(model, "state") == "POLLED"

    # Test integer fields
    int_fields = ["scheduled_time", "execution_time"]
    for field in int_fields:
        setattr(model, field, 123456)
        assert getattr(model, field) == 123456


def test_state_enum_validation_preserved():
    """Test that state field validation rules are preserved."""
    model = WorkflowScheduleExecutionModel()

    # Test valid enum values still work
    valid_states = ["POLLED", "FAILED", "EXECUTED"]

    for state in valid_states:
        model.state = state
        assert model.state == state

    # Test invalid enum values still raise ValueError (including None)
    invalid_states = ["INVALID", "RUNNING", "PENDING", "", None]

    for state in invalid_states:
        with pytest.raises(ValueError, match="Invalid"):
            model.state = state


def test_attribute_map_preserved():
    """Verify attribute_map hasn't changed for existing fields."""
    expected_attribute_map = {
        "execution_id": "executionId",
        "schedule_name": "scheduleName",
        "scheduled_time": "scheduledTime",
        "execution_time": "executionTime",
        "workflow_name": "workflowName",
        "workflow_id": "workflowId",
        "reason": "reason",
        "stack_trace": "stackTrace",
        "start_workflow_request": "startWorkflowRequest",
        "state": "state",
    }

    actual_attribute_map = WorkflowScheduleExecutionModel.attribute_map

    # Check that all expected mappings exist and are correct
    for field, expected_mapping in expected_attribute_map.items():
        assert (
            field in actual_attribute_map
        ), f"Field '{field}' missing from attribute_map"
        assert (
            actual_attribute_map[field] == expected_mapping
        ), f"Mapping for field '{field}' has changed"


def test_swagger_types_mapping_preserved():
    """Verify swagger_types mapping hasn't changed for existing fields."""
    expected_swagger_types = {
        "execution_id": "str",
        "schedule_name": "str",
        "scheduled_time": "int",
        "execution_time": "int",
        "workflow_name": "str",
        "workflow_id": "str",
        "reason": "str",
        "stack_trace": "str",
        "start_workflow_request": "StartWorkflowRequest",
        "state": "str",
    }

    actual_swagger_types = WorkflowScheduleExecutionModel.swagger_types

    # Check that all expected fields exist with correct types
    for field, expected_type in expected_swagger_types.items():
        assert (
            field in actual_swagger_types
        ), f"Field '{field}' missing from swagger_types"
        assert (
            actual_swagger_types[field] == expected_type
        ), f"Type for field '{field}' has changed"


def test_to_dict_method_preserved(valid_data):
    """Test that to_dict method works and returns expected structure."""
    model = WorkflowScheduleExecutionModel(**valid_data)
    result = model.to_dict()

    # Verify it returns a dict
    assert isinstance(result, dict)

    # Verify expected keys exist
    expected_keys = set(valid_data.keys())
    actual_keys = set(result.keys())

    assert expected_keys.issubset(
        actual_keys
    ), f"Missing keys in to_dict: {expected_keys - actual_keys}"


def test_to_str_method_preserved(valid_data):
    """Test that to_str method works."""
    model = WorkflowScheduleExecutionModel(**valid_data)
    result = model.to_str()

    assert isinstance(result, str)
    assert len(result) > 0


def test_equality_methods_preserved(valid_data):
    """Test that __eq__ and __ne__ methods work correctly."""
    model1 = WorkflowScheduleExecutionModel(**valid_data)
    model2 = WorkflowScheduleExecutionModel(**valid_data)
    model3 = WorkflowScheduleExecutionModel()

    # Test equality
    assert model1 == model2
    assert model1 != model3

    # Test inequality
    assert not (model1 != model2)
    assert model1 != model3

    # Test against non-model objects
    assert model1 != "not a model"
    assert model1 != {}


def test_repr_method_preserved(valid_data):
    """Test that __repr__ method works."""
    model = WorkflowScheduleExecutionModel(**valid_data)
    repr_result = repr(model)

    assert isinstance(repr_result, str)
    assert len(repr_result) > 0


def test_individual_field_assignment():
    """Test that individual field assignment still works."""
    model = WorkflowScheduleExecutionModel()

    # Test each field can be set and retrieved
    test_values = {
        "execution_id": "new_exec_id",
        "schedule_name": "new_schedule",
        "scheduled_time": 9999999,
        "execution_time": 8888888,
        "workflow_name": "new_workflow",
        "workflow_id": "new_wf_id",
        "reason": "new_reason",
        "stack_trace": "new_trace",
        "start_workflow_request": None,
        "state": "POLLED",
    }

    for field, value in test_values.items():
        setattr(model, field, value)
        assert getattr(model, field) == value


def test_discriminator_attribute_preserved():
    """Test that discriminator attribute exists and is None."""
    model = WorkflowScheduleExecutionModel()
    assert hasattr(model, "discriminator")
    assert model.discriminator is None
