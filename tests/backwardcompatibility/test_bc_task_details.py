import pytest

from conductor.client.http.models.task_details import TaskDetails


@pytest.fixture
def valid_data():
    """Set up test fixture with valid data for all known fields."""
    return {
        "workflow_id": "test-workflow-123",
        "task_ref_name": "test-task-ref",
        "output": {"result": "success", "data": [1, 2, 3]},
        "task_id": "test-task-456",
    }


def test_constructor_with_no_args_succeeds():
    """Test that TaskDetails can be instantiated with no arguments (all fields optional)."""
    task_details = TaskDetails()
    assert isinstance(task_details, TaskDetails)

    # All fields should be None initially
    assert task_details.workflow_id is None
    assert task_details.task_ref_name is None
    assert task_details.output is None
    assert task_details.task_id is None


def test_constructor_with_all_args_succeeds(valid_data):
    """Test that TaskDetails can be instantiated with all arguments."""
    task_details = TaskDetails(**valid_data)

    assert task_details.workflow_id == valid_data["workflow_id"]
    assert task_details.task_ref_name == valid_data["task_ref_name"]
    assert task_details.output == valid_data["output"]
    assert task_details.task_id == valid_data["task_id"]


def test_constructor_with_partial_args_succeeds():
    """Test that TaskDetails can be instantiated with partial arguments."""
    partial_data = {
        "workflow_id": "test-workflow",
        "task_id": "test-task",
    }

    task_details = TaskDetails(**partial_data)

    assert task_details.workflow_id == partial_data["workflow_id"]
    assert task_details.task_id == partial_data["task_id"]
    assert task_details.task_ref_name is None
    assert task_details.output is None


def test_all_expected_fields_exist():
    """Test that all expected fields exist and are accessible."""
    task_details = TaskDetails()

    # Test that all expected properties exist
    expected_fields = ["workflow_id", "task_ref_name", "output", "task_id"]

    for field in expected_fields:
        assert hasattr(task_details, field), f"Field '{field}' should exist"
        # Test getter works
        value = getattr(task_details, field)
        assert value is None  # Should be None by default


def test_field_types_unchanged(valid_data):
    """Test that field types haven't changed from expected types."""
    task_details = TaskDetails(**valid_data)

    # Test workflow_id type
    assert isinstance(task_details.workflow_id, str)

    # Test task_ref_name type
    assert isinstance(task_details.task_ref_name, str)

    # Test output type
    assert isinstance(task_details.output, dict)

    # Test task_id type
    assert isinstance(task_details.task_id, str)


def test_property_setters_work():
    """Test that all property setters work as expected."""
    task_details = TaskDetails()

    # Test workflow_id setter
    task_details.workflow_id = "new-workflow"
    assert task_details.workflow_id == "new-workflow"

    # Test task_ref_name setter
    task_details.task_ref_name = "new-task-ref"
    assert task_details.task_ref_name == "new-task-ref"

    # Test output setter
    new_output = {"status": "completed"}
    task_details.output = new_output
    assert task_details.output == new_output

    # Test task_id setter
    task_details.task_id = "new-task-id"
    assert task_details.task_id == "new-task-id"


def test_setters_accept_none_values(valid_data):
    """Test that setters accept None values (fields are optional)."""
    task_details = TaskDetails(**valid_data)

    # All setters should accept None
    task_details.workflow_id = None
    assert task_details.workflow_id is None

    task_details.task_ref_name = None
    assert task_details.task_ref_name is None

    task_details.output = None
    assert task_details.output is None

    task_details.task_id = None
    assert task_details.task_id is None


def test_swagger_types_attribute_exists():
    """Test that swagger_types class attribute exists and has expected structure."""
    assert hasattr(TaskDetails, "swagger_types")
    swagger_types = TaskDetails.swagger_types

    expected_types = {
        "workflow_id": "str",
        "task_ref_name": "str",
        "output": "dict(str, object)",
        "task_id": "str",
    }

    for field, expected_type in expected_types.items():
        assert field in swagger_types, f"Field '{field}' should be in swagger_types"
        assert (
            swagger_types[field] == expected_type
        ), f"Type for '{field}' should be '{expected_type}'"


def test_attribute_map_exists():
    """Test that attribute_map class attribute exists and has expected structure."""
    assert hasattr(TaskDetails, "attribute_map")
    attribute_map = TaskDetails.attribute_map

    expected_mappings = {
        "workflow_id": "workflowId",
        "task_ref_name": "taskRefName",
        "output": "output",
        "task_id": "taskId",
    }

    for field, expected_json_key in expected_mappings.items():
        assert field in attribute_map, f"Field '{field}' should be in attribute_map"
        assert (
            attribute_map[field] == expected_json_key
        ), f"JSON key for '{field}' should be '{expected_json_key}'"


def test_to_dict_method_exists_and_works(valid_data):
    """Test that to_dict method exists and returns expected structure."""
    task_details = TaskDetails(**valid_data)

    result_dict = task_details.to_dict()

    assert isinstance(result_dict, dict)

    # Check that all fields are present in the dictionary
    expected_fields = ["workflow_id", "task_ref_name", "output", "task_id"]
    for field in expected_fields:
        assert field in result_dict
        assert result_dict[field] == getattr(task_details, field)


def test_to_str_method_exists(valid_data):
    """Test that to_str method exists and returns a string."""
    task_details = TaskDetails(**valid_data)

    result_str = task_details.to_str()
    assert isinstance(result_str, str)
    assert len(result_str) > 0


def test_repr_method_exists(valid_data):
    """Test that __repr__ method exists and returns a string."""
    task_details = TaskDetails(**valid_data)

    repr_str = repr(task_details)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


def test_equality_methods_exist_and_work(valid_data):
    """Test that __eq__ and __ne__ methods exist and work correctly."""
    task_details1 = TaskDetails(**valid_data)
    task_details2 = TaskDetails(**valid_data)
    task_details3 = TaskDetails(workflow_id="different")

    # Test equality
    assert task_details1 == task_details2
    assert task_details1 != task_details3

    # Test inequality
    assert not (task_details1 != task_details2)
    assert task_details1 != task_details3

    # Test comparison with non-TaskDetails object
    assert task_details1 != "not a task details"
    assert task_details1 != "not a task details"


def test_discriminator_attribute_exists():
    """Test that discriminator attribute exists and is set to None."""
    task_details = TaskDetails()
    assert hasattr(task_details, "discriminator")
    assert task_details.discriminator is None


def test_output_dict_type_flexibility():
    """Test that output field accepts various dict structures."""
    task_details = TaskDetails()

    # Empty dict
    task_details.output = {}
    assert task_details.output == {}

    # Simple dict
    simple_dict = {"key": "value"}
    task_details.output = simple_dict
    assert task_details.output == simple_dict

    # Complex nested dict
    complex_dict = {
        "results": [1, 2, 3],
        "metadata": {"count": 3, "status": "success"},
        "nested": {"deep": {"value": True}},
    }
    task_details.output = complex_dict
    assert task_details.output == complex_dict


def test_backward_compatibility_with_unknown_constructor_args():
    """Test that constructor gracefully handles unknown arguments (future additions)."""
    # This tests that adding new fields won't break existing instantiation
    try:
        # Try to create with valid arguments only - the current constructor
        # should work with known arguments
        task_details = TaskDetails(workflow_id="test", task_id="test")
        # Should not raise an exception
        assert isinstance(task_details, TaskDetails)

        # Test that unknown arguments would cause TypeError (expected behavior)
        # This documents current behavior for future reference
        with pytest.raises(TypeError):
            TaskDetails(
                workflow_id="test",
                unknown_future_field="value",  # This should fail
            )

    except Exception as e:
        pytest.fail(f"Constructor with valid arguments should not fail: {e}")


def test_field_assignment_after_construction(valid_data):
    """Test that fields can be assigned after object construction."""
    task_details = TaskDetails()

    # Test assignment of all fields after construction
    task_details.workflow_id = valid_data["workflow_id"]
    task_details.task_ref_name = valid_data["task_ref_name"]
    task_details.output = valid_data["output"]
    task_details.task_id = valid_data["task_id"]

    # Verify assignments worked
    assert task_details.workflow_id == valid_data["workflow_id"]
    assert task_details.task_ref_name == valid_data["task_ref_name"]
    assert task_details.output == valid_data["output"]
    assert task_details.task_id == valid_data["task_id"]
