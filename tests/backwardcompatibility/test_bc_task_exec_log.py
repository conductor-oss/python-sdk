from conductor.client.http.models import TaskExecLog


def test_constructor_with_no_args():
    """Test that constructor works with no arguments (all fields optional)"""
    log = TaskExecLog()

    # Verify all fields exist and are None by default
    assert log.log is None
    assert log.task_id is None
    assert log.created_time is None
    assert log.discriminator is None


def test_constructor_with_all_args():
    """Test constructor with all arguments"""
    test_log = "Test log message"
    test_task_id = "task_123"
    test_created_time = 1640995200

    log = TaskExecLog(
        log=test_log,
        task_id=test_task_id,
        created_time=test_created_time,
    )

    assert log.log == test_log
    assert log.task_id == test_task_id
    assert log.created_time == test_created_time


def test_constructor_with_partial_args():
    """Test constructor with partial arguments"""
    test_log = "Partial test"

    log = TaskExecLog(log=test_log)

    assert log.log == test_log
    assert log.task_id is None
    assert log.created_time is None


def test_existing_fields_exist():
    """Verify all expected fields exist and are accessible"""
    log = TaskExecLog()

    # Test field existence via hasattr
    assert hasattr(log, "log")
    assert hasattr(log, "task_id")
    assert hasattr(log, "created_time")
    assert hasattr(log, "discriminator")


def test_property_getters():
    """Test that all property getters work correctly"""
    log = TaskExecLog()

    # Should not raise AttributeError
    _ = log.log
    _ = log.task_id
    _ = log.created_time


def test_property_setters():
    """Test that all property setters work correctly"""
    log = TaskExecLog()

    # Test log setter
    log.log = "New log message"
    assert log.log == "New log message"

    # Test task_id setter
    log.task_id = "new_task_456"
    assert log.task_id == "new_task_456"

    # Test created_time setter
    log.created_time = 1641081600
    assert log.created_time == 1641081600


def test_field_types_unchanged():
    """Verify field types remain as expected (string types in swagger_types)"""
    # Check swagger_types class attribute exists and contains expected types
    assert hasattr(TaskExecLog, "swagger_types")

    expected_types = {
        "log": "str",
        "task_id": "str",
        "created_time": "int",
    }

    for field, expected_type in expected_types.items():
        assert field in TaskExecLog.swagger_types
        assert TaskExecLog.swagger_types[field] == expected_type


def test_attribute_map_unchanged():
    """Verify attribute_map remains unchanged for API compatibility"""
    assert hasattr(TaskExecLog, "attribute_map")

    expected_map = {
        "log": "log",
        "task_id": "taskId",
        "created_time": "createdTime",
    }

    for field, json_key in expected_map.items():
        assert field in TaskExecLog.attribute_map
        assert TaskExecLog.attribute_map[field] == json_key


def test_to_dict_method_exists():
    """Test that to_dict method exists and works"""
    log = TaskExecLog(
        log="Test log",
        task_id="task_789",
        created_time=1641168000,
    )

    result = log.to_dict()

    assert isinstance(result, dict)
    assert result["log"] == "Test log"
    assert result["task_id"] == "task_789"
    assert result["created_time"] == 1641168000


def test_to_str_method_exists():
    """Test that to_str method exists and works"""
    log = TaskExecLog(log="Test")

    result = log.to_str()
    assert isinstance(result, str)


def test_repr_method_exists():
    """Test that __repr__ method exists and works"""
    log = TaskExecLog(log="Test")

    result = repr(log)
    assert isinstance(result, str)


def test_equality_methods_exist():
    """Test that equality methods exist and work correctly"""
    log1 = TaskExecLog(log="Test", task_id="123")
    log2 = TaskExecLog(log="Test", task_id="123")
    log3 = TaskExecLog(log="Different", task_id="456")

    # Test __eq__
    assert log1 == log2
    assert log1 != log3

    # Test __ne__
    assert not (log1 != log2)
    assert log1 != log3


def test_none_values_handling():
    """Test that None values are handled correctly"""
    log = TaskExecLog()

    # Setting None should work
    log.log = None
    log.task_id = None
    log.created_time = None

    assert log.log is None
    assert log.task_id is None
    assert log.created_time is None


def test_discriminator_field_exists():
    """Test that discriminator field exists and defaults to None"""
    log = TaskExecLog()
    assert hasattr(log, "discriminator")
    assert log.discriminator is None


def test_private_attributes_exist():
    """Test that private attributes are properly initialized"""
    log = TaskExecLog()

    # These should exist as they're set in __init__
    assert hasattr(log, "_log")
    assert hasattr(log, "_task_id")
    assert hasattr(log, "_created_time")


def test_constructor_parameter_names_unchanged():
    """Test that constructor accepts the expected parameter names"""
    # This should not raise TypeError
    log = TaskExecLog(
        log="test_log",
        task_id="test_task_id",
        created_time=12345,
    )

    assert log.log == "test_log"
    assert log.task_id == "test_task_id"
    assert log.created_time == 12345


def test_serialization_compatibility():
    """Test that serialization produces expected structure"""
    log = TaskExecLog(
        log="Serialization test",
        task_id="serial_123",
        created_time=1641254400,
    )

    dict_result = log.to_dict()

    # Verify expected keys exist
    expected_keys = {"log", "task_id", "created_time"}
    assert expected_keys.issubset(dict_result.keys())

    # Verify values are correctly serialized
    assert dict_result["log"] == "Serialization test"
    assert dict_result["task_id"] == "serial_123"
    assert dict_result["created_time"] == 1641254400
