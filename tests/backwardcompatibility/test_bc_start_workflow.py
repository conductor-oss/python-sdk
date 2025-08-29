from conductor.client.http.models.start_workflow_request import StartWorkflowRequest


def test_constructor_accepts_all_current_parameters():
    """Test that constructor accepts all current parameters without errors."""
    # Test with all parameters (current behavior)
    workflow = StartWorkflowRequest(
        name="test_workflow",
        version=1,
        correlation_id="test_correlation_123",
        input={"param1": "value1", "param2": 42},
        task_to_domain={"task1": "domain1", "task2": "domain2"},
    )

    # Verify all values are set correctly
    assert workflow.name == "test_workflow"
    assert workflow.version == 1
    assert workflow.correlation_id == "test_correlation_123"
    assert workflow.input == {"param1": "value1", "param2": 42}
    assert workflow.task_to_domain == {"task1": "domain1", "task2": "domain2"}


def test_constructor_accepts_no_parameters():
    """Test that constructor works with no parameters (all optional)."""
    workflow = StartWorkflowRequest()

    # All fields should be None initially
    assert workflow.name is None
    assert workflow.version is None
    assert workflow.correlation_id is None
    assert workflow.input is None
    assert workflow.task_to_domain is None


def test_constructor_accepts_partial_parameters():
    """Test that constructor works with partial parameters."""
    workflow = StartWorkflowRequest(name="partial_test", version=2)

    assert workflow.name == "partial_test"
    assert workflow.version == 2
    assert workflow.correlation_id is None
    assert workflow.input is None
    assert workflow.task_to_domain is None


def test_all_required_fields_exist():
    """Test that all expected fields exist and are accessible."""
    workflow = StartWorkflowRequest()

    # Test field existence through property access
    assert hasattr(workflow, "name")
    assert hasattr(workflow, "version")
    assert hasattr(workflow, "correlation_id")
    assert hasattr(workflow, "input")
    assert hasattr(workflow, "task_to_domain")

    # Test that properties are callable
    _ = workflow.name
    _ = workflow.version
    _ = workflow.correlation_id
    _ = workflow.input
    _ = workflow.task_to_domain


def test_field_setters_work():
    """Test that all field setters work correctly."""
    workflow = StartWorkflowRequest()

    # Test setting each field
    workflow.name = "setter_test"
    workflow.version = 5
    workflow.correlation_id = "setter_correlation"
    workflow.input = {"setter_key": "setter_value"}
    workflow.task_to_domain = {"setter_task": "setter_domain"}

    # Verify values were set
    assert workflow.name == "setter_test"
    assert workflow.version == 5
    assert workflow.correlation_id == "setter_correlation"
    assert workflow.input == {"setter_key": "setter_value"}
    assert workflow.task_to_domain == {"setter_task": "setter_domain"}


def test_field_types_preserved():
    """Test that field types match expected types."""
    workflow = StartWorkflowRequest(
        name="type_test",
        version=10,
        correlation_id="type_correlation",
        input={"key": "value"},
        task_to_domain={"task": "domain"},
    )

    # Test type expectations based on swagger_types
    assert isinstance(workflow.name, str)
    assert isinstance(workflow.version, int)
    assert isinstance(workflow.correlation_id, str)
    assert isinstance(workflow.input, dict)
    assert isinstance(workflow.task_to_domain, dict)


def test_none_values_accepted():
    """Test that None values are accepted for all fields."""
    workflow = StartWorkflowRequest()

    # Set all fields to None
    workflow.name = None
    workflow.version = None
    workflow.correlation_id = None
    workflow.input = None
    workflow.task_to_domain = None

    # Verify None values are preserved
    assert workflow.name is None
    assert workflow.version is None
    assert workflow.correlation_id is None
    assert workflow.input is None
    assert workflow.task_to_domain is None


def test_to_dict_method_exists_and_works():
    """Test that to_dict method exists and preserves all fields."""
    workflow = StartWorkflowRequest(
        name="dict_test",
        version=3,
        correlation_id="dict_correlation",
        input={"dict_key": "dict_value"},
        task_to_domain={"dict_task": "dict_domain"},
    )

    result_dict = workflow.to_dict()

    # Verify to_dict returns a dictionary
    assert isinstance(result_dict, dict)

    # Verify all fields are present in dict
    assert result_dict["name"] == "dict_test"
    assert result_dict["version"] == 3
    assert result_dict["correlation_id"] == "dict_correlation"
    assert result_dict["input"] == {"dict_key": "dict_value"}
    assert result_dict["task_to_domain"] == {"dict_task": "dict_domain"}


def test_to_str_method_exists():
    """Test that to_str method exists and returns string."""
    workflow = StartWorkflowRequest(name="str_test")
    result = workflow.to_str()
    assert isinstance(result, str)


def test_repr_method_exists():
    """Test that __repr__ method exists and returns string."""
    workflow = StartWorkflowRequest(name="repr_test")
    result = repr(workflow)
    assert isinstance(result, str)


def test_equality_methods_exist():
    """Test that equality methods exist and work."""
    workflow1 = StartWorkflowRequest(name="eq_test", version=1)
    workflow2 = StartWorkflowRequest(name="eq_test", version=1)
    workflow3 = StartWorkflowRequest(name="different", version=2)

    # Test __eq__
    assert workflow1 == workflow2
    assert not (workflow1 == workflow3)

    # Test __ne__
    assert not (workflow1 != workflow2)
    assert workflow1 != workflow3


def test_swagger_types_attribute_exists():
    """Test that swagger_types class attribute exists and has expected structure."""
    expected_types = {
        "name": "str",
        "version": "int",
        "correlation_id": "str",
        "input": "dict(str, object)",
        "task_to_domain": "dict(str, str)",
    }

    assert hasattr(StartWorkflowRequest, "swagger_types")
    assert isinstance(StartWorkflowRequest.swagger_types, dict)

    # Verify all expected fields are present in swagger_types
    for field, expected_type in expected_types.items():
        assert field in StartWorkflowRequest.swagger_types
        assert StartWorkflowRequest.swagger_types[field] == expected_type


def test_attribute_map_exists():
    """Test that attribute_map class attribute exists and has expected structure."""
    expected_mapping = {
        "name": "name",
        "version": "version",
        "correlation_id": "correlationId",
        "input": "input",
        "task_to_domain": "taskToDomain",
    }

    assert hasattr(StartWorkflowRequest, "attribute_map")
    assert isinstance(StartWorkflowRequest.attribute_map, dict)

    # Verify all expected mappings are present
    for attr, json_key in expected_mapping.items():
        assert attr in StartWorkflowRequest.attribute_map
        assert StartWorkflowRequest.attribute_map[attr] == json_key


def test_input_dict_accepts_various_value_types():
    """Test that input dict accepts various object types as specified."""
    workflow = StartWorkflowRequest()

    # Test various value types in input dict
    complex_input = {
        "string_val": "test",
        "int_val": 42,
        "float_val": 3.14,
        "bool_val": True,
        "list_val": [1, 2, 3],
        "dict_val": {"nested": "value"},
        "none_val": None,
    }

    workflow.input = complex_input
    assert workflow.input == complex_input


def test_task_to_domain_dict_string_values():
    """Test that task_to_domain accepts string-to-string mappings."""
    workflow = StartWorkflowRequest()

    task_mapping = {
        "task1": "domain1",
        "task2": "domain2",
        "task_with_underscore": "domain_with_underscore",
    }

    workflow.task_to_domain = task_mapping
    assert workflow.task_to_domain == task_mapping
