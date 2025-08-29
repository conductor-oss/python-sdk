import inspect
import json

import pytest

from conductor.client.http.models import WorkflowDef
from conductor.client.http.models.workflow_def import to_workflow_def


@pytest.fixture
def required_constructor_fields():
    """Set up test fixture with core required fields that must always exist."""
    return {
        "name",
        "tasks",
    }  # Based on analysis: name and tasks are set without conditionals


@pytest.fixture
def expected_fields():
    """Set up test fixture with all existing fields that must remain available."""
    return {
        "owner_app",
        "create_time",
        "update_time",
        "created_by",
        "updated_by",
        "name",
        "description",
        "version",
        "tasks",
        "input_parameters",
        "output_parameters",
        "failure_workflow",
        "schema_version",
        "restartable",
        "workflow_status_listener_enabled",
        "workflow_status_listener_sink",
        "owner_email",
        "timeout_policy",
        "timeout_seconds",
        "variables",
        "input_template",
        "input_schema",
        "output_schema",
        "enforce_schema",
    }


@pytest.fixture
def expected_field_types():
    """Set up test fixture with expected field types that must not change."""
    return {
        "owner_app": str,
        "create_time": int,
        "update_time": int,
        "created_by": str,
        "updated_by": str,
        "name": str,
        "description": str,
        "version": int,
        "tasks": list,  # list[WorkflowTask]
        "input_parameters": list,  # list[str]
        "output_parameters": dict,  # dict(str, object)
        "failure_workflow": str,
        "schema_version": int,
        "restartable": bool,
        "workflow_status_listener_enabled": bool,
        "workflow_status_listener_sink": str,
        "owner_email": str,
        "timeout_policy": str,
        "timeout_seconds": int,
        "variables": dict,  # dict(str, object)
        "input_template": dict,  # dict(str, object)
        "input_schema": object,  # SchemaDef
        "output_schema": object,  # SchemaDef
        "enforce_schema": bool,
    }


@pytest.fixture
def timeout_policy_allowed_values():
    """Set up test fixture with validation rules that must be preserved."""
    return ["TIME_OUT_WF", "ALERT_ONLY"]


@pytest.fixture
def simple_task():
    """Set up test fixture with a simple task dict instead of Mock for better compatibility."""
    return {
        "name": "test_task",
        "type": "SIMPLE",
        "taskReferenceName": "test_ref",
    }


def test_constructor_with_minimal_params_works():
    """Test that constructor works with minimal parameters (backward compatibility)."""
    # This should work as it always has
    workflow = WorkflowDef(name="test_workflow")
    assert workflow.name == "test_workflow"
    assert workflow.tasks is not None  # Should default to empty list


def test_constructor_with_all_legacy_params_works(simple_task):
    """Test that constructor accepts all existing parameters."""
    # All these parameters should continue to work
    workflow = WorkflowDef(
        owner_app="test_app",
        name="test_workflow",
        description="test description",
        version=1,
        tasks=[simple_task],
        input_parameters=["param1"],
        output_parameters={"output1": "value1"},
        failure_workflow="failure_wf",
        schema_version=2,
        restartable=True,
        workflow_status_listener_enabled=False,
        workflow_status_listener_sink="sink",
        owner_email="test@example.com",
        timeout_policy="TIME_OUT_WF",
        timeout_seconds=3600,
        variables={"var1": "value1"},
        input_template={"template": "value"},
        enforce_schema=True,
    )

    # Verify all values are set correctly
    assert workflow.owner_app == "test_app"
    assert workflow.name == "test_workflow"
    assert workflow.description == "test description"
    assert workflow.version == 1
    assert workflow.tasks == [simple_task]
    assert workflow.input_parameters == ["param1"]
    assert workflow.output_parameters == {"output1": "value1"}
    assert workflow.failure_workflow == "failure_wf"
    assert workflow.schema_version == 2
    assert workflow.restartable
    assert not workflow.workflow_status_listener_enabled
    assert workflow.workflow_status_listener_sink == "sink"
    assert workflow.owner_email == "test@example.com"
    assert workflow.timeout_policy == "TIME_OUT_WF"
    assert workflow.timeout_seconds == 3600
    assert workflow.variables == {"var1": "value1"}
    assert workflow.input_template == {"template": "value"}
    assert workflow.enforce_schema


def test_all_expected_fields_exist_as_properties(expected_fields):
    """Test that all expected fields exist as properties."""
    workflow = WorkflowDef(name="test")

    for field_name in expected_fields:
        # Property should exist
        assert hasattr(
            workflow, field_name
        ), f"Field '{field_name}' is missing from WorkflowDef"

        # Should be able to get the property
        try:
            getattr(workflow, field_name)
        except Exception as e:
            pytest.fail(f"Cannot get property '{field_name}': {e}")


def test_all_expected_fields_have_setters(
    expected_fields, expected_field_types, mocker
):
    """Test that all expected fields have working setters."""
    workflow = WorkflowDef(name="test")

    # Test data for each field type - with special handling for validated fields
    test_values = {
        str: "test_string",
        int: 42,
        bool: True,
        list: ["item1", "item2"],
        dict: {"key": "value"},
        object: mocker.Mock(),  # For SchemaDef fields
    }

    # Special test values for fields with validation
    special_test_values = {
        "timeout_policy": "TIME_OUT_WF",  # Use valid enum value
    }

    for field_name in expected_fields:
        expected_type = expected_field_types[field_name]

        # Use special test value if available, otherwise use default for type
        if field_name in special_test_values:
            test_value = special_test_values[field_name]
        else:
            test_value = test_values[expected_type]

        # Should be able to set the property
        try:
            setattr(workflow, field_name, test_value)
            retrieved_value = getattr(workflow, field_name)

            # Value should be set correctly
            if (
                expected_type is not object
            ):  # Skip exact equality check for mock objects
                assert (
                    retrieved_value == test_value
                ), f"Field '{field_name}' value not set correctly"
        except Exception as e:
            pytest.fail(f"Cannot set property '{field_name}': {e}")


def test_field_types_unchanged(expected_field_types, simple_task):
    """Test that field types haven't changed."""
    workflow = WorkflowDef(name="test")

    # Set test values and verify types
    test_data = {
        "owner_app": "test_app",
        "create_time": 1234567890,
        "update_time": 1234567890,
        "created_by": "user",
        "updated_by": "user",
        "name": "test_workflow",
        "description": "description",
        "version": 1,
        "tasks": [simple_task],
        "input_parameters": ["param"],
        "output_parameters": {"key": "value"},
        "failure_workflow": "failure",
        "schema_version": 2,
        "restartable": True,
        "workflow_status_listener_enabled": False,
        "workflow_status_listener_sink": "sink",
        "owner_email": "test@test.com",
        "timeout_policy": "TIME_OUT_WF",
        "timeout_seconds": 3600,
        "variables": {"var": "value"},
        "input_template": {"template": "value"},
        "enforce_schema": True,
    }

    for field_name, test_value in test_data.items():
        setattr(workflow, field_name, test_value)
        retrieved_value = getattr(workflow, field_name)
        expected_type = expected_field_types[field_name]

        assert isinstance(
            retrieved_value, expected_type
        ), f"Field '{field_name}' type changed. Expected {expected_type}, got {type(retrieved_value)}"


def test_timeout_policy_validation_preserved(timeout_policy_allowed_values):
    """Test that timeout_policy validation rules are preserved."""
    workflow = WorkflowDef(name="test")

    # Valid values should work
    for valid_value in timeout_policy_allowed_values:
        workflow.timeout_policy = valid_value
        assert workflow.timeout_policy == valid_value

    # Invalid values should raise ValueError
    invalid_values = ["INVALID", "TIME_OUT", "ALERT", ""]
    for invalid_value in invalid_values:
        with pytest.raises(ValueError, match="Invalid"):
            workflow.timeout_policy = invalid_value


def test_tasks_property_default_behavior():
    """Test that tasks property returns empty list when None (current behavior)."""
    workflow = WorkflowDef(name="test")
    workflow._tasks = None

    # Should return empty list, not None
    assert workflow.tasks == []
    assert isinstance(workflow.tasks, list)


def test_swagger_types_structure_preserved(expected_fields):
    """Test that swagger_types class attribute is preserved."""
    assert hasattr(WorkflowDef, "swagger_types")
    swagger_types = WorkflowDef.swagger_types

    # All expected fields should be in swagger_types
    for field_name in expected_fields:
        assert (
            field_name in swagger_types
        ), f"Field '{field_name}' missing from swagger_types"


def test_attribute_map_structure_preserved(expected_fields):
    """Test that attribute_map class attribute is preserved."""
    assert hasattr(WorkflowDef, "attribute_map")
    attribute_map = WorkflowDef.attribute_map

    # All expected fields should be in attribute_map
    for field_name in expected_fields:
        assert (
            field_name in attribute_map
        ), f"Field '{field_name}' missing from attribute_map"


def test_to_dict_method_preserved(simple_task):
    """Test that to_dict method works and includes all fields."""
    workflow = WorkflowDef(
        name="test_workflow",
        description="test",
        version=1,
        tasks=[simple_task],
    )

    # Method should exist and work
    result = workflow.to_dict()
    assert isinstance(result, dict)

    # Should contain expected fields that were set
    assert "name" in result
    assert "description" in result
    assert "version" in result
    assert "tasks" in result


def test_to_json_method_preserved():
    """Test that toJSON method works."""
    workflow = WorkflowDef(name="test_workflow")

    # Method should exist and return serializable data
    json_result = workflow.toJSON()

    # The result should be either a string or a dict (depending on implementation)
    assert isinstance(
        json_result, (str, dict)
    ), f"toJSON should return str or dict, got {type(json_result)}"

    # If it's a string, it should be valid JSON
    if isinstance(json_result, str):
        parsed = json.loads(json_result)
        assert isinstance(parsed, dict)
    else:
        # If it's already a dict, it should be JSON-serializable
        json_string = json.dumps(json_result)
        assert isinstance(json_string, str)


def test_equality_methods_preserved():
    """Test that __eq__ and __ne__ methods work."""
    workflow1 = WorkflowDef(name="test")
    workflow2 = WorkflowDef(name="test")
    workflow3 = WorkflowDef(name="different")

    # Equal objects
    assert workflow1 == workflow2
    assert not (workflow1 != workflow2)

    # Different objects
    assert workflow1 != workflow3
    assert workflow1 != workflow3


def test_to_workflow_def_function_preserved():
    """Test that to_workflow_def helper function works."""
    # Test with JSON data
    json_data = {
        "name": "test_workflow",
        "description": "test description",
        "version": 1,
    }

    workflow = to_workflow_def(json_data=json_data)
    assert isinstance(workflow, WorkflowDef)
    assert workflow.name == "test_workflow"

    # Test with string data
    json_string = json.dumps(json_data)
    workflow2 = to_workflow_def(data=json_string)
    assert isinstance(workflow2, WorkflowDef)
    assert workflow2.name == "test_workflow"


def test_new_fields_should_not_break_existing_functionality(simple_task):
    """Test that adding new fields doesn't break existing functionality."""
    # This test ensures that if new fields are added to the model,
    # existing code continues to work
    workflow = WorkflowDef(name="test")

    # All existing functionality should still work
    workflow.description = "test description"
    workflow.version = 1
    workflow.tasks = [simple_task]

    # Core methods should work
    dict_result = workflow.to_dict()
    json_result = workflow.toJSON()
    str_result = str(workflow)

    assert isinstance(dict_result, dict)
    assert isinstance(json_result, (str, dict))  # Handle both possible return types
    assert isinstance(str_result, str)


def test_constructor_parameter_names_unchanged():
    """Test that constructor parameter names haven't changed."""

    sig = inspect.signature(WorkflowDef.__init__)
    param_names = set(sig.parameters.keys()) - {"self"}  # Exclude 'self'

    # All expected parameters should exist
    expected_params = {
        "owner_app",
        "create_time",
        "update_time",
        "created_by",
        "updated_by",
        "name",
        "description",
        "version",
        "tasks",
        "input_parameters",
        "output_parameters",
        "failure_workflow",
        "schema_version",
        "restartable",
        "workflow_status_listener_enabled",
        "workflow_status_listener_sink",
        "owner_email",
        "timeout_policy",
        "timeout_seconds",
        "variables",
        "input_template",
        "input_schema",
        "output_schema",
        "enforce_schema",
    }

    # All expected parameters must be present
    missing_params = expected_params - param_names
    assert len(missing_params) == 0, f"Missing constructor parameters: {missing_params}"
