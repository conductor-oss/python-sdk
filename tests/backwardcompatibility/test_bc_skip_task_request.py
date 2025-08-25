import pytest

from conductor.client.adapters.models.skip_task_request_adapter import SkipTaskRequestAdapter


@pytest.fixture
def valid_task_input():
    """Set up test fixture with valid task input."""
    return {
        "inputKey1": "inputValue1",
        "inputKey2": {"nested": "value"},
        "inputKey3": 123,
    }


@pytest.fixture
def valid_task_output():
    """Set up test fixture with valid task output."""
    return {
        "outputKey1": "outputValue1",
        "outputKey2": ["list", "value"],
        "outputKey3": True,
    }


def test_constructor_with_no_parameters():
    """Test that constructor works with no parameters (backward compatibility)."""
    request = SkipTaskRequestAdapter()

    # Verify default state
    assert request.task_input is None
    assert request.task_output is None


def test_constructor_with_task_input_only(valid_task_input):
    """Test constructor with only task_input parameter."""
    request = SkipTaskRequestAdapter(task_input=valid_task_input)

    assert request.task_input == valid_task_input
    assert request.task_output is None


def test_constructor_with_task_output_only(valid_task_output):
    """Test constructor with only task_output parameter."""
    request = SkipTaskRequestAdapter(task_output=valid_task_output)

    assert request.task_input is None
    assert request.task_output == valid_task_output


def test_constructor_with_both_parameters(valid_task_input, valid_task_output):
    """Test constructor with both parameters."""
    request = SkipTaskRequestAdapter(
        task_input=valid_task_input, task_output=valid_task_output
    )

    assert request.task_input == valid_task_input
    assert request.task_output == valid_task_output


def test_task_input_property_exists():
    """Test that task_input property exists and is accessible."""
    request = SkipTaskRequestAdapter()

    # Property should exist and be gettable
    assert hasattr(request, "task_input")
    assert request.task_input is None


def test_task_output_property_exists():
    """Test that task_output property exists and is accessible."""
    request = SkipTaskRequestAdapter()

    # Property should exist and be gettable
    assert hasattr(request, "task_output")
    assert request.task_output is None


def test_task_input_setter_functionality(valid_task_input):
    """Test that task_input setter works correctly."""
    request = SkipTaskRequestAdapter()

    # Test setting valid dict
    request.task_input = valid_task_input
    assert request.task_input == valid_task_input

    # Test setting None
    request.task_input = None
    assert request.task_input is None

    # Test setting empty dict
    request.task_input = {}
    assert request.task_input == {}


def test_task_output_setter_functionality(valid_task_output):
    """Test that task_output setter works correctly."""
    request = SkipTaskRequestAdapter()

    # Test setting valid dict
    request.task_output = valid_task_output
    assert request.task_output == valid_task_output

    # Test setting None
    request.task_output = None
    assert request.task_output is None

    # Test setting empty dict
    request.task_output = {}
    assert request.task_output == {}


def test_task_input_type_compatibility():
    """Test that task_input accepts dict types as expected."""
    request = SkipTaskRequestAdapter()

    # Test various dict types that should be compatible
    test_inputs = [
        {},  # Empty dict
        {"key": "value"},  # Simple dict
        {"nested": {"key": "value"}},  # Nested dict
        {"mixed": ["list", 123, True, None]},  # Mixed types
    ]

    for test_input in test_inputs:
        request.task_input = test_input
        assert request.task_input == test_input


def test_task_output_type_compatibility():
    """Test that task_output accepts dict types as expected."""
    request = SkipTaskRequestAdapter()

    # Test various dict types that should be compatible
    test_outputs = [
        {},  # Empty dict
        {"result": "success"},  # Simple dict
        {"data": {"processed": True}},  # Nested dict
        {"results": [{"id": 1}, {"id": 2}]},  # Complex structure
    ]

    for test_output in test_outputs:
        request.task_output = test_output
        assert request.task_output == test_output


def test_swagger_types_attribute_exists():
    """Test that swagger_types class attribute exists and has expected structure."""
    assert hasattr(SkipTaskRequestAdapter, "swagger_types")
    swagger_types = SkipTaskRequestAdapter.swagger_types

    # Verify expected fields exist in swagger_types
    assert "task_input" in swagger_types
    assert "task_output" in swagger_types

    # Verify types are as expected (dict(str, object))
    assert swagger_types["task_input"] == "dict(str, object)"
    assert swagger_types["task_output"] == "dict(str, object)"


def test_attribute_map_exists():
    """Test that attribute_map class attribute exists and has expected structure."""
    assert hasattr(SkipTaskRequestAdapter, "attribute_map")
    attribute_map = SkipTaskRequestAdapter.attribute_map

    # Verify expected mappings exist
    assert "task_input" in attribute_map
    assert "task_output" in attribute_map

    # Verify JSON key mappings
    assert attribute_map["task_input"] == "taskInput"
    assert attribute_map["task_output"] == "taskOutput"


def test_to_dict_method_exists_and_works(valid_task_input, valid_task_output):
    """Test that to_dict method exists and produces expected output."""
    request = SkipTaskRequestAdapter(
        task_input=valid_task_input, task_output=valid_task_output
    )

    assert hasattr(request, "to_dict")
    result = request.to_dict()

    # Verify it returns a dict
    assert isinstance(result, dict)

    # Verify expected keys exist
    assert "task_input" in result
    assert "task_output" in result

    # Verify values match
    assert result["task_input"] == valid_task_input
    assert result["task_output"] == valid_task_output


def test_to_str_method_exists():
    """Test that to_str method exists and returns string."""
    request = SkipTaskRequestAdapter()

    assert hasattr(request, "to_str")
    result = request.to_str()
    assert isinstance(result, str)


def test_repr_method_exists():
    """Test that __repr__ method exists and returns string."""
    request = SkipTaskRequestAdapter()

    result = repr(request)
    assert isinstance(result, str)


def test_equality_methods_exist_and_work(valid_task_input, valid_task_output):
    """Test that equality methods exist and work correctly."""
    request1 = SkipTaskRequestAdapter(task_input=valid_task_input)
    request2 = SkipTaskRequestAdapter(task_input=valid_task_input)
    request3 = SkipTaskRequestAdapter(task_output=valid_task_output)

    # Test equality
    assert request1 == request2
    assert request1 != request3

    # Test inequality
    assert not (request1 != request2)
    assert request1 != request3


def test_discriminator_attribute_exists():
    """Test that discriminator attribute exists (Swagger requirement)."""
    request = SkipTaskRequestAdapter()
    assert hasattr(request, "discriminator")
    assert request.discriminator is None


def test_private_attributes_exist():
    """Test that private attributes exist (internal implementation)."""
    request = SkipTaskRequestAdapter()

    # These private attributes should exist for internal implementation
    assert hasattr(request, "_task_input")
    assert hasattr(request, "_task_output")


def test_backward_compatible_dict_assignment():
    """Test assignment of various dict-like objects for backward compatibility."""
    request = SkipTaskRequestAdapter()

    # Test that we can assign different dict-like structures
    # that might have been valid in previous versions
    test_cases = [
        # Empty structures
        ({}, {}),
        # Simple key-value pairs
        ({"input": "test"}, {"output": "result"}),
        # Complex nested structures
        (
            {"workflow": {"id": "wf1", "tasks": [1, 2, 3]}},
            {"result": {"status": "completed", "data": {"count": 5}}},
        ),
    ]

    for task_input, task_output in test_cases:
        request.task_input = task_input
        request.task_output = task_output

        assert request.task_input == task_input
        assert request.task_output == task_output


def test_none_assignment_preserved(valid_task_input, valid_task_output):
    """Test that None assignment behavior is preserved."""
    request = SkipTaskRequestAdapter(
        task_input=valid_task_input, task_output=valid_task_output
    )

    # Should be able to reset to None
    request.task_input = None
    request.task_output = None

    assert request.task_input is None
    assert request.task_output is None
