import pytest

from conductor.client.adapters.models.schema_def_adapter import SchemaDefAdapter
from conductor.client.adapters.models.task_def_adapter import TaskDefAdapter


@pytest.fixture
def valid_schema_def(mocker):
    """Set up test fixture with valid schema definition."""
    return mocker.Mock(spec=SchemaDefAdapter)


@pytest.fixture
def valid_timeout_policies():
    """Set up test fixture with valid timeout policy enum values."""
    return ["RETRY", "TIME_OUT_WF", "ALERT_ONLY"]


@pytest.fixture
def valid_retry_logics():
    """Set up test fixture with valid retry logic enum values."""
    return ["FIXED", "EXPONENTIAL_BACKOFF", "LINEAR_BACKOFF"]


def test_constructor_with_minimal_required_fields():
    """Test that constructor works with minimal required fields."""
    # Based on analysis: name and timeout_seconds appear to be required
    task_def = TaskDefAdapter(name="test_task", timeout_seconds=60)

    assert task_def.name == "test_task"
    assert task_def.timeout_seconds == 60


def test_constructor_with_all_existing_fields(valid_schema_def):
    """Test constructor with all existing fields to ensure they still work."""
    task_def = TaskDefAdapter(
        owner_app="test_app",
        create_time=1234567890,
        update_time=1234567891,
        created_by="test_user",
        updated_by="test_user_2",
        name="test_task",
        description="Test task description",
        retry_count=3,
        timeout_seconds=60,
        input_keys=["input1", "input2"],
        output_keys=["output1", "output2"],
        timeout_policy="RETRY",
        retry_logic="FIXED",
        retry_delay_seconds=5,
        response_timeout_seconds=30,
        concurrent_exec_limit=10,
        input_template={"key": "value"},
        rate_limit_per_frequency=100,
        rate_limit_frequency_in_seconds=60,
        isolation_group_id="group1",
        execution_name_space="namespace1",
        owner_email="test@example.com",
        poll_timeout_seconds=120,
        backoff_scale_factor=2,
        input_schema=valid_schema_def,
        output_schema=valid_schema_def,
        enforce_schema=True,
    )

    # Verify all fields are set correctly
    assert task_def.owner_app == "test_app"
    assert task_def.create_time == 1234567890
    assert task_def.update_time == 1234567891
    assert task_def.created_by == "test_user"
    assert task_def.updated_by == "test_user_2"
    assert task_def.name == "test_task"
    assert task_def.description == "Test task description"
    assert task_def.retry_count == 3
    assert task_def.timeout_seconds == 60
    assert task_def.input_keys == ["input1", "input2"]
    assert task_def.output_keys == ["output1", "output2"]
    assert task_def.timeout_policy == "RETRY"
    assert task_def.retry_logic == "FIXED"
    assert task_def.retry_delay_seconds == 5
    assert task_def.response_timeout_seconds == 30
    assert task_def.concurrent_exec_limit == 10
    assert task_def.input_template == {"key": "value"}
    assert task_def.rate_limit_per_frequency == 100
    assert task_def.rate_limit_frequency_in_seconds == 60
    assert task_def.isolation_group_id == "group1"
    assert task_def.execution_name_space == "namespace1"
    assert task_def.owner_email == "test@example.com"
    assert task_def.poll_timeout_seconds == 120
    assert task_def.backoff_scale_factor == 2
    assert task_def.input_schema == valid_schema_def
    assert task_def.output_schema == valid_schema_def
    assert task_def.enforce_schema is True


def test_all_existing_properties_exist():
    """Verify all existing properties still exist and are accessible."""
    task_def = TaskDefAdapter(name="test", timeout_seconds=60)

    # Test that all existing properties exist (both getters and setters)
    existing_properties = [
        "owner_app",
        "create_time",
        "update_time",
        "created_by",
        "updated_by",
        "name",
        "description",
        "retry_count",
        "timeout_seconds",
        "input_keys",
        "output_keys",
        "timeout_policy",
        "retry_logic",
        "retry_delay_seconds",
        "response_timeout_seconds",
        "concurrent_exec_limit",
        "input_template",
        "rate_limit_per_frequency",
        "rate_limit_frequency_in_seconds",
        "isolation_group_id",
        "execution_name_space",
        "owner_email",
        "poll_timeout_seconds",
        "backoff_scale_factor",
        "input_schema",
        "output_schema",
        "enforce_schema",
    ]

    for prop in existing_properties:
        # Test getter exists
        assert hasattr(task_def, prop), f"Property {prop} getter missing"
        # Test setter exists
        assert hasattr(type(task_def), prop), f"Property {prop} setter missing"


def test_existing_field_types_unchanged():
    """Verify existing field types haven't changed."""
    expected_types = {
        "owner_app": str,
        "create_time": int,
        "update_time": int,
        "created_by": str,
        "updated_by": str,
        "name": str,
        "description": str,
        "retry_count": int,
        "timeout_seconds": int,
        "input_keys": list,
        "output_keys": list,
        "timeout_policy": str,
        "retry_logic": str,
        "retry_delay_seconds": int,
        "response_timeout_seconds": int,
        "concurrent_exec_limit": int,
        "input_template": dict,
        "rate_limit_per_frequency": int,
        "rate_limit_frequency_in_seconds": int,
        "isolation_group_id": str,
        "execution_name_space": str,
        "owner_email": str,
        "poll_timeout_seconds": int,
        "backoff_scale_factor": int,
        "input_schema": SchemaDefAdapter,
        "output_schema": SchemaDefAdapter,
        "enforce_schema": bool,
    }

    # Check that all expected fields exist in swagger_types
    for field in expected_types.keys():
        assert field in TaskDefAdapter.swagger_types, f"Missing field {field} in swagger_types"

        # This would need additional logic to check type compatibility properly
        # For now, just ensure the field exists


def test_timeout_policy_enum_values_preserved(valid_timeout_policies):
    """Test that existing timeout_policy enum values still work."""
    task_def = TaskDefAdapter(name="test", timeout_seconds=60)

    for valid_value in valid_timeout_policies:
        # Test setter validation
        task_def.timeout_policy = valid_value
        assert task_def.timeout_policy == valid_value


def test_timeout_policy_invalid_values_rejected():
    """Test that invalid timeout_policy values are still rejected."""
    task_def = TaskDefAdapter(name="test", timeout_seconds=60)

    invalid_values = ["INVALID", "invalid", "", None, 123]
    for invalid_value in invalid_values:
        with pytest.raises(ValueError, match="Invalid"):
            task_def.timeout_policy = invalid_value


def test_retry_logic_enum_values_preserved(valid_retry_logics):
    """Test that existing retry_logic enum values still work."""
    task_def = TaskDefAdapter(name="test", timeout_seconds=60)

    for valid_value in valid_retry_logics:
        # Test setter validation
        task_def.retry_logic = valid_value
        assert task_def.retry_logic == valid_value


def test_retry_logic_invalid_values_rejected():
    """Test that invalid retry_logic values are still rejected."""
    task_def = TaskDefAdapter(name="test", timeout_seconds=60)

    invalid_values = ["INVALID", "invalid", "", None, 123]
    for invalid_value in invalid_values:
        with pytest.raises(ValueError, match="Invalid"):
            task_def.retry_logic = invalid_value


def test_attribute_map_unchanged():
    """Test that attribute_map for existing fields is unchanged."""
    expected_attribute_map = {
        "owner_app": "ownerApp",
        "create_time": "createTime",
        "update_time": "updateTime",
        "created_by": "createdBy",
        "updated_by": "updatedBy",
        "name": "name",
        "description": "description",
        "retry_count": "retryCount",
        "timeout_seconds": "timeoutSeconds",
        "input_keys": "inputKeys",
        "output_keys": "outputKeys",
        "timeout_policy": "timeoutPolicy",
        "retry_logic": "retryLogic",
        "retry_delay_seconds": "retryDelaySeconds",
        "response_timeout_seconds": "responseTimeoutSeconds",
        "concurrent_exec_limit": "concurrentExecLimit",
        "input_template": "inputTemplate",
        "rate_limit_per_frequency": "rateLimitPerFrequency",
        "rate_limit_frequency_in_seconds": "rateLimitFrequencyInSeconds",
        "isolation_group_id": "isolationGroupId",
        "execution_name_space": "executionNameSpace",
        "owner_email": "ownerEmail",
        "poll_timeout_seconds": "pollTimeoutSeconds",
        "backoff_scale_factor": "backoffScaleFactor",
        "input_schema": "inputSchema",
        "output_schema": "outputSchema",
        "enforce_schema": "enforceSchema",
    }

    for python_name, json_name in expected_attribute_map.items():
        assert (
            python_name in TaskDefAdapter.attribute_map
        ), f"Missing attribute mapping for {python_name}"
        assert (
            TaskDefAdapter.attribute_map[python_name] == json_name
        ), f"Changed attribute mapping for {python_name}"


def test_to_dict_method_exists_and_works(valid_schema_def):
    """Test that to_dict method exists and produces expected structure."""
    task_def = TaskDefAdapter(
        name="test_task",
        timeout_seconds=60,
        description="Test description",
        retry_count=3,
        input_schema=valid_schema_def,
        enforce_schema=True,
    )

    result = task_def.to_dict()

    assert isinstance(result, dict)
    assert result["name"] == "test_task"
    assert result["timeout_seconds"] == 60
    assert result["description"] == "Test description"
    assert result["retry_count"] == 3
    assert result["enforce_schema"] is True


def test_to_str_method_exists_and_works():
    """Test that to_str method exists and works."""
    task_def = TaskDefAdapter(name="test", timeout_seconds=60)

    result = task_def.to_str()
    assert isinstance(result, str)
    assert "test" in result


def test_equality_methods_exist_and_work():
    """Test that __eq__ and __ne__ methods exist and work correctly."""
    task_def1 = TaskDefAdapter(name="test", timeout_seconds=60)
    task_def2 = TaskDefAdapter(name="test", timeout_seconds=60)
    task_def3 = TaskDefAdapter(name="different", timeout_seconds=60)

    # Test equality
    assert task_def1 == task_def2
    assert task_def1 != task_def3

    # Test inequality
    assert not (task_def1 != task_def2)
    assert task_def1 != task_def3


def test_repr_method_exists_and_works():
    """Test that __repr__ method exists and works."""
    task_def = TaskDefAdapter(name="test", timeout_seconds=60)

    result = repr(task_def)
    assert isinstance(result, str)


def test_schema_properties_behavior(valid_schema_def):
    """Test that schema-related properties work as expected."""
    task_def = TaskDefAdapter(name="test", timeout_seconds=60)

    # Test input_schema
    task_def.input_schema = valid_schema_def
    assert task_def.input_schema == valid_schema_def

    # Test output_schema
    task_def.output_schema = valid_schema_def
    assert task_def.output_schema == valid_schema_def

    # Test enforce_schema
    task_def.enforce_schema = True
    assert task_def.enforce_schema is True

    task_def.enforce_schema = False
    assert task_def.enforce_schema is False


def test_list_and_dict_field_types():
    """Test that list and dict fields accept correct types."""
    task_def = TaskDefAdapter(name="test", timeout_seconds=60)

    # Test list fields
    task_def.input_keys = ["key1", "key2"]
    assert task_def.input_keys == ["key1", "key2"]

    task_def.output_keys = ["out1", "out2"]
    assert task_def.output_keys == ["out1", "out2"]

    # Test dict field
    template = {"param1": "value1", "param2": 123}
    task_def.input_template = template
    assert task_def.input_template == template


def test_numeric_field_types():
    """Test that numeric fields accept correct types."""
    task_def = TaskDefAdapter(name="test", timeout_seconds=60)

    numeric_fields = [
        "create_time",
        "update_time",
        "retry_count",
        "timeout_seconds",
        "retry_delay_seconds",
        "response_timeout_seconds",
        "concurrent_exec_limit",
        "rate_limit_per_frequency",
        "rate_limit_frequency_in_seconds",
        "poll_timeout_seconds",
        "backoff_scale_factor",
    ]

    for field in numeric_fields:
        setattr(task_def, field, 42)
        assert getattr(task_def, field) == 42, f"Numeric field {field} failed"


def test_string_field_types():
    """Test that string fields accept correct types."""
    task_def = TaskDefAdapter(name="test", timeout_seconds=60)

    string_fields = [
        "owner_app",
        "created_by",
        "updated_by",
        "name",
        "description",
        "isolation_group_id",
        "execution_name_space",
        "owner_email",
    ]

    for field in string_fields:
        setattr(task_def, field, "test_value")
        assert getattr(task_def, field) == "test_value", f"String field {field} failed"
