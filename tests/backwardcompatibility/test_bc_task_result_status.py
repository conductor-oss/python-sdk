from enum import Enum

import pytest

from conductor.client.http.models import TaskResultStatus


@pytest.fixture
def required_enum_values():
    """Set up test fixture with expected enum values that must always exist."""
    # These are the enum values that existed in the original version
    # and must remain for backward compatibility
    return {
        "COMPLETED",
        "FAILED",
        "FAILED_WITH_TERMINAL_ERROR",
        "IN_PROGRESS",
    }


@pytest.fixture
def required_string_values():
    """Set up test fixture with expected string values that must always exist."""
    return {
        "COMPLETED",
        "FAILED",
        "FAILED_WITH_TERMINAL_ERROR",
        "IN_PROGRESS",
    }


def test_all_required_enum_values_exist(required_enum_values):
    """Test that all originally existing enum values still exist."""
    actual_enum_names = {member.name for member in TaskResultStatus}

    missing_values = required_enum_values - actual_enum_names
    assert len(missing_values) == 0, (
        f"Missing required enum values: {missing_values}. "
        f"Removing enum values breaks backward compatibility."
    )


def test_enum_values_unchanged(required_enum_values):
    """Test that existing enum values haven't changed their string representation."""
    for enum_name in required_enum_values:
        # Verify the enum member exists
        assert hasattr(
            TaskResultStatus, enum_name
        ), f"Enum value {enum_name} no longer exists"

        enum_member = getattr(TaskResultStatus, enum_name)

        # Test the string value matches expected
        expected_string_value = enum_name
        assert (
            enum_member.value == expected_string_value
        ), f"Enum {enum_name} value changed from '{expected_string_value}' to '{enum_member.value}'"


def test_str_method_backward_compatibility(required_enum_values):
    """Test that __str__ method returns expected values for existing enums."""
    for enum_name in required_enum_values:
        enum_member = getattr(TaskResultStatus, enum_name)
        expected_str = enum_name
        actual_str = str(enum_member)

        assert (
            actual_str == expected_str
        ), f"str({enum_name}) changed from '{expected_str}' to '{actual_str}'"


def test_enum_inheritance_unchanged():
    """Test that TaskResultStatus still inherits from expected base classes."""
    # Verify it's still an Enum
    assert issubclass(
        TaskResultStatus, Enum
    ), "TaskResultStatus no longer inherits from Enum"

    # Verify it's still a str enum (can be used as string)
    assert issubclass(
        TaskResultStatus, str
    ), "TaskResultStatus no longer inherits from str"


def test_enum_can_be_constructed_from_string(required_string_values):
    """Test that existing enum values can still be constructed from strings."""
    for string_value in required_string_values:
        try:
            enum_instance = TaskResultStatus(string_value)
            assert (
                enum_instance.value == string_value
            ), f"TaskResultStatus('{string_value}') does not have expected value"
        except (ValueError, TypeError) as e:  # noqa: PERF203
            pytest.fail(
                f"TaskResultStatus('{string_value}') construction failed: {e}. "
                f"This breaks backward compatibility."
            )


def test_enum_equality_with_strings(required_enum_values):
    """Test that enum values can still be compared with strings."""
    for enum_name in required_enum_values:
        enum_member = getattr(TaskResultStatus, enum_name)

        # Test equality with string value
        assert (
            enum_member == enum_name
        ), f"TaskResultStatus.{enum_name} != '{enum_name}' (string comparison failed)"


def test_enum_serialization_compatibility(required_enum_values):
    """Test that enum values serialize to expected strings for JSON/API compatibility."""
    for enum_name in required_enum_values:
        enum_member = getattr(TaskResultStatus, enum_name)

        # Test that the enum value can be used in JSON-like contexts
        serialized = str(enum_member)
        assert (
            serialized == enum_name
        ), f"Serialization of {enum_name} changed from '{enum_name}' to '{serialized}'"


def test_enum_membership_operations(required_enum_values):
    """Test that existing enum values work with membership operations."""
    all_members = list(TaskResultStatus)
    all_member_names = [member.name for member in all_members]

    for required_name in required_enum_values:
        assert (
            required_name in all_member_names
        ), f"Required enum value {required_name} not found in TaskResultStatus members"


def test_addition_tolerance(required_enum_values):
    """Test that the enum can have additional values (forward compatibility)."""
    # This test ensures that if new enum values are added,
    # the existing functionality still works
    actual_values = {member.name for member in TaskResultStatus}

    # Verify we have at least the required values
    assert required_enum_values.issubset(
        actual_values
    ), f"Missing required enum values: {required_enum_values - actual_values}"

    # Additional values are allowed (this should not fail)
    additional_values = actual_values - required_enum_values
    if additional_values:
        # Log that additional values exist (this is OK for backward compatibility)
        print(f"INFO: Additional enum values found (this is OK): {additional_values}")


def test_enum_immutability(required_enum_values):
    """Test that enum values are immutable."""
    for enum_name in required_enum_values:
        enum_member = getattr(TaskResultStatus, enum_name)

        # Attempt to modify the enum value should fail
        with pytest.raises((AttributeError, TypeError)):
            enum_member.value = "MODIFIED"
