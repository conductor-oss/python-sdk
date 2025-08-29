import pytest

from conductor.client.http.models.action import Action


@pytest.fixture
def baseline_swagger_types():
    """Baseline swagger types for backward compatibility testing."""
    return {
        "action": "str",
        "start_workflow": "StartWorkflowRequest",
        "complete_task": "TaskDetails",
        "fail_task": "TaskDetails",
        "expand_inline_json": "bool",
    }


@pytest.fixture
def baseline_attribute_map():
    """Baseline attribute map for backward compatibility testing."""
    return {
        "action": "action",
        "start_workflow": "start_workflow",
        "complete_task": "complete_task",
        "fail_task": "fail_task",
        "expand_inline_json": "expandInlineJSON",
    }


@pytest.fixture
def baseline_allowed_action_values():
    """Baseline allowed action values for backward compatibility testing."""
    return ["start_workflow", "complete_task", "fail_task"]


def test_required_fields_exist(baseline_swagger_types):
    """Verify all baseline fields still exist in the model."""
    action = Action()

    # Check that all baseline swagger_types fields exist
    for field_name in baseline_swagger_types.keys():
        assert hasattr(action, field_name), f"Missing required field: {field_name}"
        assert hasattr(
            action, f"_{field_name}"
        ), f"Missing private field: _{field_name}"


def test_swagger_types_compatibility(baseline_swagger_types):
    """Verify existing swagger_types haven't changed."""
    current_swagger_types = Action.swagger_types

    # Check all baseline types are preserved
    for field_name, expected_type in baseline_swagger_types.items():
        assert (
            field_name in current_swagger_types
        ), f"Field {field_name} removed from swagger_types"
        assert (
            current_swagger_types[field_name] == expected_type
        ), f"Field {field_name} type changed from {expected_type} to {current_swagger_types[field_name]}"


def test_attribute_map_compatibility(baseline_attribute_map):
    """Verify existing attribute_map hasn't changed."""
    current_attribute_map = Action.attribute_map

    # Check all baseline mappings are preserved
    for field_name, expected_json_key in baseline_attribute_map.items():
        assert (
            field_name in current_attribute_map
        ), f"Field {field_name} removed from attribute_map"
        assert (
            current_attribute_map[field_name] == expected_json_key
        ), f"Field {field_name} JSON mapping changed from {expected_json_key} to {current_attribute_map[field_name]}"


def test_constructor_parameters_compatibility():
    """Verify constructor accepts all baseline parameters."""
    # Should be able to create Action with all baseline parameters
    try:
        action = Action(
            action="start_workflow",
            start_workflow=None,
            complete_task=None,
            fail_task=None,
            expand_inline_json=True,
        )
        assert isinstance(action, Action)
    except TypeError as e:
        pytest.fail(
            f"Constructor signature changed - baseline parameters rejected: {e}"
        )


def test_property_getters_exist(baseline_swagger_types):
    """Verify all baseline property getters still exist."""
    for field_name in baseline_swagger_types.keys():
        # Check getter property exists
        assert hasattr(Action, field_name), f"Missing property getter: {field_name}"
        # Check it's actually a property
        assert isinstance(
            getattr(Action, field_name), property
        ), f"{field_name} is not a property"


def test_property_setters_exist(baseline_swagger_types):
    """Verify all baseline property setters still exist."""
    for field_name in baseline_swagger_types.keys():
        # Check setter exists by trying to access it
        prop = getattr(Action, field_name)
        assert prop.fset is not None, f"Missing property setter: {field_name}"


def test_action_enum_validation_compatibility(baseline_allowed_action_values):
    """Verify action field validation rules are preserved."""
    action = Action()

    # Test that baseline allowed values still work
    for allowed_value in baseline_allowed_action_values:
        try:
            action.action = allowed_value
            assert action.action == allowed_value
        except ValueError:  # noqa: PERF203
            pytest.fail(
                f"Previously allowed action value '{allowed_value}' now rejected"
            )

    # Test that invalid values are still rejected
    with pytest.raises(ValueError, match="Invalid value for"):
        action.action = "invalid_action"


def test_field_type_assignments():
    """Verify baseline field types can still be assigned."""
    action = Action()

    # Test string assignment to action
    action.action = "start_workflow"
    assert action.action == "start_workflow"

    # Test boolean assignment to expand_inline_json
    action.expand_inline_json = True
    assert action.expand_inline_json is True

    action.expand_inline_json = False
    assert action.expand_inline_json is False


def test_to_dict_method_compatibility(baseline_swagger_types):
    """Verify to_dict method still works and includes baseline fields."""
    action = Action(action="complete_task", expand_inline_json=True)

    result_dict = action.to_dict()

    # Check method still works
    assert isinstance(result_dict, dict)

    # Check baseline fields are included in output
    expected_fields = set(baseline_swagger_types.keys())
    actual_fields = set(result_dict.keys())

    assert expected_fields.issubset(
        actual_fields
    ), f"Missing baseline fields in to_dict output: {expected_fields - actual_fields}"


def test_to_str_method_compatibility():
    """Verify to_str method still works."""
    action = Action(action="fail_task")

    try:
        str_result = action.to_str()
        assert isinstance(str_result, str)
    except Exception as e:
        pytest.fail(f"to_str method failed: {e}")


def test_equality_methods_compatibility():
    """Verify __eq__ and __ne__ methods still work."""
    action1 = Action(action="start_workflow", expand_inline_json=True)
    action2 = Action(action="start_workflow", expand_inline_json=True)
    action3 = Action(action="complete_task", expand_inline_json=False)

    try:
        # Test equality
        assert action1 == action2
        assert not (action1 == action3)

        # Test inequality
        assert not (action1 != action2)
        assert action1 != action3
    except Exception as e:
        pytest.fail(f"Equality methods failed: {e}")


def test_repr_method_compatibility():
    """Verify __repr__ method still works."""
    action = Action(action="start_workflow")

    try:
        repr_result = repr(action)
        assert isinstance(repr_result, str)
    except Exception as e:
        pytest.fail(f"__repr__ method failed: {e}")
