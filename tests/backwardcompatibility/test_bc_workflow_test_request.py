import pytest

from conductor.client.adapters.models.workflow_test_request_adapter import WorkflowTestRequestAdapter


@pytest.fixture
def mock_workflow_def(mocker):
    """Set up test fixture with mock workflow definition."""
    return mocker.Mock()


@pytest.fixture
def mock_task_mock(mocker):
    """Set up test fixture with mock task mock."""
    return mocker.Mock()


def test_class_exists_and_instantiable():
    """Test that the WorkflowTestRequestAdapter class exists and can be instantiated."""
    # Should be able to create instance with just required field
    instance = WorkflowTestRequestAdapter(name="test_workflow")
    assert isinstance(instance, WorkflowTestRequestAdapter)
    assert instance.name == "test_workflow"


def test_swagger_types_structure():
    """Test that swagger_types dictionary contains all expected fields with correct types."""
    expected_swagger_types = {
        "correlation_id": "str",
        "created_by": "str",
        "external_input_payload_storage_path": "str",
        "input": "dict(str, object)",
        "name": "str",
        "priority": "int",
        "sub_workflow_test_request": "dict(str, WorkflowTestRequest)",
        "task_ref_to_mock_output": "dict(str, list[TaskMock])",
        "task_to_domain": "dict(str, str)",
        "version": "int",
        "workflow_def": "WorkflowDef",
    }

    # Check that all expected fields exist
    for field, expected_type in expected_swagger_types.items():
        assert (
            field in WorkflowTestRequestAdapter.swagger_types
        ), f"Field '{field}' missing from swagger_types"
        assert (
            WorkflowTestRequestAdapter.swagger_types[field] == expected_type
        ), f"Field '{field}' has incorrect type in swagger_types"


def test_attribute_map_structure():
    """Test that attribute_map dictionary contains all expected mappings."""
    expected_attribute_map = {
        "correlation_id": "correlationId",
        "created_by": "createdBy",
        "external_input_payload_storage_path": "externalInputPayloadStoragePath",
        "input": "input",
        "name": "name",
        "priority": "priority",
        "sub_workflow_test_request": "subWorkflowTestRequest",
        "task_ref_to_mock_output": "taskRefToMockOutput",
        "task_to_domain": "taskToDomain",
        "version": "version",
        "workflow_def": "workflowDef",
    }

    # Check that all expected mappings exist
    for field, expected_json_key in expected_attribute_map.items():
        assert (
            field in WorkflowTestRequestAdapter.attribute_map
        ), f"Field '{field}' missing from attribute_map"
        assert (
            WorkflowTestRequestAdapter.attribute_map[field] == expected_json_key
        ), f"Field '{field}' has incorrect JSON mapping in attribute_map"


def test_all_expected_properties_exist():
    """Test that all expected properties exist and are accessible."""
    instance = WorkflowTestRequestAdapter(name="test")

    expected_properties = [
        "correlation_id",
        "created_by",
        "external_input_payload_storage_path",
        "input",
        "name",
        "priority",
        "sub_workflow_test_request",
        "task_ref_to_mock_output",
        "task_to_domain",
        "version",
        "workflow_def",
    ]

    for prop in expected_properties:
        # Test getter exists
        assert hasattr(instance, prop), f"Property '{prop}' getter missing"

        # Test property is accessible (shouldn't raise exception)
        try:
            getattr(instance, prop)
        except Exception as e:
            pytest.fail(f"Property '{prop}' getter failed: {e}")


def test_all_expected_setters_exist():
    """Test that all expected property setters exist and work."""
    instance = WorkflowTestRequestAdapter(name="test")

    # Test string fields
    string_fields = [
        "correlation_id",
        "created_by",
        "external_input_payload_storage_path",
        "name",
    ]
    for field in string_fields:
        try:
            setattr(instance, field, "test_value")
            assert (
                getattr(instance, field) == "test_value"
            ), f"String field '{field}' setter/getter failed"
        except Exception as e:  # noqa: PERF203
            pytest.fail(f"String field '{field}' setter failed: {e}")

    # Test integer fields
    int_fields = ["priority", "version"]
    for field in int_fields:
        try:
            setattr(instance, field, 42)
            assert (
                getattr(instance, field) == 42
            ), f"Integer field '{field}' setter/getter failed"
        except Exception as e:  # noqa: PERF203
            pytest.fail(f"Integer field '{field}' setter failed: {e}")

    # Test dict fields
    dict_fields = ["input", "task_to_domain"]
    for field in dict_fields:
        try:
            test_dict = {"key": "value"}
            setattr(instance, field, test_dict)
            assert (
                getattr(instance, field) == test_dict
            ), f"Dict field '{field}' setter/getter failed"
        except Exception as e:  # noqa: PERF203
            pytest.fail(f"Dict field '{field}' setter failed: {e}")


def test_name_field_validation():
    """Test that name field validation still works as expected."""
    # Name is required - should raise ValueError when set to None
    instance = WorkflowTestRequestAdapter(name="test")

    with pytest.raises(ValueError, match="Invalid"):
        instance.name = None


def test_constructor_with_all_optional_parameters(mock_workflow_def, mock_task_mock):
    """Test that constructor accepts all expected optional parameters."""
    # This tests that the constructor signature hasn't changed
    try:
        instance = WorkflowTestRequestAdapter(
            correlation_id="corr_123",
            created_by="user_123",
            external_input_payload_storage_path="/path/to/payload",
            input={"key": "value"},
            name="test_workflow",
            priority=1,
            sub_workflow_test_request={"sub": mock_task_mock},
            task_ref_to_mock_output={"task": [mock_task_mock]},
            task_to_domain={"task": "domain"},
            version=2,
            workflow_def=mock_workflow_def,
        )

        # Verify all values were set correctly
        assert instance.correlation_id == "corr_123"
        assert instance.created_by == "user_123"
        assert instance.external_input_payload_storage_path == "/path/to/payload"
        assert instance.input == {"key": "value"}
        assert instance.name == "test_workflow"
        assert instance.priority == 1
        assert instance.sub_workflow_test_request is not None
        assert instance.task_ref_to_mock_output is not None
        assert instance.task_to_domain == {"task": "domain"}
        assert instance.version == 2
        assert instance.workflow_def == mock_workflow_def

    except Exception as e:
        pytest.fail(f"Constructor with all parameters failed: {e}")


def test_constructor_with_minimal_parameters():
    """Test that constructor works with minimal required parameters."""
    try:
        instance = WorkflowTestRequestAdapter(name="minimal_test")
        assert instance.name == "minimal_test"

        # All other fields should be None (default values)
        assert instance.correlation_id is None
        assert instance.created_by is None
        assert instance.external_input_payload_storage_path is None
        assert instance.input is None
        assert instance.priority is None
        assert instance.sub_workflow_test_request is None
        assert instance.task_ref_to_mock_output is None
        assert instance.task_to_domain is None
        assert instance.version is None
        assert instance.workflow_def is None

    except Exception as e:
        pytest.fail(f"Constructor with minimal parameters failed: {e}")


def test_to_dict_method_exists():
    """Test that to_dict method exists and returns expected structure."""
    instance = WorkflowTestRequestAdapter(name="test", priority=1)

    assert hasattr(instance, "to_dict"), "to_dict method missing"

    try:
        result = instance.to_dict()
        assert isinstance(result, dict), "to_dict should return a dictionary"

        # Should contain the fields we set
        assert "name" in result
        assert "priority" in result
        assert result["name"] == "test"
        assert result["priority"] == 1

    except Exception as e:
        pytest.fail(f"to_dict method failed: {e}")


def test_to_str_method_exists():
    """Test that to_str method exists and works."""
    instance = WorkflowTestRequestAdapter(name="test")

    assert hasattr(instance, "to_str"), "to_str method missing"

    try:
        result = instance.to_str()
        assert isinstance(result, str), "to_str should return a string"
    except Exception as e:
        pytest.fail(f"to_str method failed: {e}")


def test_repr_method_exists():
    """Test that __repr__ method exists and works."""
    instance = WorkflowTestRequestAdapter(name="test")

    try:
        result = repr(instance)
        assert isinstance(result, str), "__repr__ should return a string"
    except Exception as e:
        pytest.fail(f"__repr__ method failed: {e}")


def test_equality_methods_exist():
    """Test that __eq__ and __ne__ methods exist and work."""
    instance1 = WorkflowTestRequestAdapter(name="test")
    instance2 = WorkflowTestRequestAdapter(name="test")
    instance3 = WorkflowTestRequestAdapter(name="different")

    try:
        # Test equality
        assert instance1 == instance2, "__eq__ method should work"
        assert not (instance1 == instance3), "__eq__ method should work"

        # Test inequality
        assert not (instance1 != instance2), "__ne__ method should work"
        assert instance1 != instance3, "__ne__ method should work"

    except Exception as e:
        pytest.fail(f"Equality methods failed: {e}")


def test_discriminator_attribute_exists():
    """Test that discriminator attribute exists (part of the model structure)."""
    instance = WorkflowTestRequestAdapter(name="test")

    assert hasattr(instance, "discriminator"), "discriminator attribute missing"
    # Should be None by default
    assert instance.discriminator is None


def test_backward_compatibility_with_new_fields():
    """Test that the model can handle new fields being added without breaking."""
    # This test simulates what happens when new fields are added to the model
    instance = WorkflowTestRequestAdapter(name="test")

    # The model should still work with all existing functionality
    # even if new fields are added to swagger_types and attribute_map

    # Test that adding arbitrary attributes doesn't break the model
    try:
        instance.new_field = "new_value"  # This should work (Python allows this)
        assert instance.new_field == "new_value"
    except Exception as e:
        # If this fails, it means the model has become more restrictive
        pytest.fail(f"Model became more restrictive - new attributes not allowed: {e}")
