import pytest

from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.workflow_state_update import WorkflowStateUpdate


@pytest.fixture
def mock_task_result():
    """Set up test fixture with mock TaskResult."""
    return TaskResult()


@pytest.fixture
def test_variables():
    """Set up test fixture with test variables."""
    return {"key1": "value1", "key2": 123}


def test_constructor_with_no_arguments():
    """Test that constructor works with no arguments (all fields optional)."""
    obj = WorkflowStateUpdate()

    # All fields should be None initially
    assert obj.task_reference_name is None
    assert obj.task_result is None
    assert obj.variables is None


def test_constructor_with_all_arguments(mock_task_result, test_variables):
    """Test constructor with all known arguments."""
    obj = WorkflowStateUpdate(
        task_reference_name="test_task",
        task_result=mock_task_result,
        variables=test_variables,
    )

    assert obj.task_reference_name == "test_task"
    assert obj.task_result == mock_task_result
    assert obj.variables == test_variables


def test_constructor_with_partial_arguments(mock_task_result, test_variables):
    """Test constructor with partial arguments."""
    # Test with only task_reference_name
    obj1 = WorkflowStateUpdate(task_reference_name="test_task")
    assert obj1.task_reference_name == "test_task"
    assert obj1.task_result is None
    assert obj1.variables is None

    # Test with only task_result
    obj2 = WorkflowStateUpdate(task_result=mock_task_result)
    assert obj2.task_reference_name is None
    assert obj2.task_result == mock_task_result
    assert obj2.variables is None

    # Test with only variables
    obj3 = WorkflowStateUpdate(variables=test_variables)
    assert obj3.task_reference_name is None
    assert obj3.task_result is None
    assert obj3.variables == test_variables


def test_field_existence():
    """Test that all expected fields exist and are accessible."""
    obj = WorkflowStateUpdate()

    # Test field existence via hasattr
    assert hasattr(obj, "task_reference_name")
    assert hasattr(obj, "task_result")
    assert hasattr(obj, "variables")

    # Test private attribute existence
    assert hasattr(obj, "_task_reference_name")
    assert hasattr(obj, "_task_result")
    assert hasattr(obj, "_variables")


def test_field_types_via_assignment(mock_task_result, test_variables):
    """Test field type expectations through assignment."""
    obj = WorkflowStateUpdate()

    # Test task_reference_name expects string
    obj.task_reference_name = "test_string"
    assert obj.task_reference_name == "test_string"
    assert isinstance(obj.task_reference_name, str)

    # Test task_result expects TaskResult
    obj.task_result = mock_task_result
    assert obj.task_result == mock_task_result
    assert isinstance(obj.task_result, TaskResult)

    # Test variables expects dict
    obj.variables = test_variables
    assert obj.variables == test_variables
    assert isinstance(obj.variables, dict)


def test_property_getters(mock_task_result, test_variables):
    """Test that property getters work correctly."""
    obj = WorkflowStateUpdate(
        task_reference_name="test_task",
        task_result=mock_task_result,
        variables=test_variables,
    )

    # Test getters return correct values
    assert obj.task_reference_name == "test_task"
    assert obj.task_result == mock_task_result
    assert obj.variables == test_variables


def test_property_setters(mock_task_result):
    """Test that property setters work correctly."""
    obj = WorkflowStateUpdate()

    # Test setters
    obj.task_reference_name = "new_task"
    obj.task_result = mock_task_result
    obj.variables = {"new_key": "new_value"}

    assert obj.task_reference_name == "new_task"
    assert obj.task_result == mock_task_result
    assert obj.variables == {"new_key": "new_value"}


def test_none_assignment(mock_task_result, test_variables):
    """Test that None can be assigned to all fields."""
    obj = WorkflowStateUpdate(
        task_reference_name="test",
        task_result=mock_task_result,
        variables=test_variables,
    )

    # Set all to None
    obj.task_reference_name = None
    obj.task_result = None
    obj.variables = None

    assert obj.task_reference_name is None
    assert obj.task_result is None
    assert obj.variables is None


def test_swagger_metadata_exists():
    """Test that swagger metadata attributes exist."""
    # Test class-level swagger attributes
    assert hasattr(WorkflowStateUpdate, "swagger_types")
    assert hasattr(WorkflowStateUpdate, "attribute_map")

    # Test swagger_types structure
    expected_swagger_types = {
        "task_reference_name": "str",
        "task_result": "TaskResult",
        "variables": "dict(str, object)",
    }
    assert WorkflowStateUpdate.swagger_types == expected_swagger_types

    # Test attribute_map structure
    expected_attribute_map = {
        "task_reference_name": "taskReferenceName",
        "task_result": "taskResult",
        "variables": "variables",
    }
    assert WorkflowStateUpdate.attribute_map == expected_attribute_map


def test_to_dict_method(mock_task_result, test_variables):
    """Test that to_dict method works correctly."""
    obj = WorkflowStateUpdate(
        task_reference_name="test_task",
        task_result=mock_task_result,
        variables=test_variables,
    )

    result_dict = obj.to_dict()

    assert isinstance(result_dict, dict)
    assert "task_reference_name" in result_dict
    assert "task_result" in result_dict
    assert "variables" in result_dict


def test_to_str_method():
    """Test that to_str method works correctly."""
    obj = WorkflowStateUpdate(task_reference_name="test_task")

    str_result = obj.to_str()
    assert isinstance(str_result, str)


def test_repr_method():
    """Test that __repr__ method works correctly."""
    obj = WorkflowStateUpdate(task_reference_name="test_task")

    repr_result = repr(obj)
    assert isinstance(repr_result, str)


def test_equality_methods():
    """Test equality and inequality methods."""
    obj1 = WorkflowStateUpdate(
        task_reference_name="test_task", variables={"key": "value"}
    )
    obj2 = WorkflowStateUpdate(
        task_reference_name="test_task", variables={"key": "value"}
    )
    obj3 = WorkflowStateUpdate(task_reference_name="different_task")

    # Test equality
    assert obj1 == obj2
    assert obj1 != obj3

    # Test inequality
    assert not (obj1 != obj2)
    assert obj1 != obj3

    # Test equality with non-WorkflowStateUpdate object
    assert obj1 != "not_a_workflow_state_update"


def test_variables_dict_type_flexibility():
    """Test that variables field accepts various dict value types."""
    obj = WorkflowStateUpdate()

    # Test with various value types
    test_variables = {
        "string_value": "test",
        "int_value": 123,
        "float_value": 45.67,
        "bool_value": True,
        "list_value": [1, 2, 3],
        "dict_value": {"nested": "value"},
        "none_value": None,
    }

    obj.variables = test_variables
    assert obj.variables == test_variables


def test_field_assignment_independence(mock_task_result):
    """Test that field assignments don't affect each other."""
    obj = WorkflowStateUpdate()

    # Set fields independently
    obj.task_reference_name = "task1"
    assert obj.task_reference_name == "task1"
    assert obj.task_result is None
    assert obj.variables is None

    obj.task_result = mock_task_result
    assert obj.task_reference_name == "task1"
    assert obj.task_result == mock_task_result
    assert obj.variables is None

    obj.variables = {"key": "value"}
    assert obj.task_reference_name == "task1"
    assert obj.task_result == mock_task_result
    assert obj.variables == {"key": "value"}
