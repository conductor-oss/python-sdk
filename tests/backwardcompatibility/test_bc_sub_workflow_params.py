import pytest

from conductor.client.http.models.sub_workflow_params import SubWorkflowParams


@pytest.fixture
def mock_workflow_def(mocker):
    """Set up test fixture with mock workflow definition."""
    mock_def = mocker.MagicMock()
    mock_def.to_dict.return_value = {"mock": "workflow"}
    return mock_def


@pytest.fixture
def valid_data(mock_workflow_def):
    """Set up test fixture with valid data for all existing fields."""
    return {
        "name": "test_workflow",
        "version": 1,
        "task_to_domain": {"task1": "domain1", "task2": "domain2"},
        "workflow_definition": mock_workflow_def,
    }


def test_constructor_with_no_parameters():
    """Test that constructor works with no parameters (backward compatibility)."""
    obj = SubWorkflowParams()

    # Verify all existing fields are accessible
    assert obj.name is None
    assert obj.version is None
    assert obj.task_to_domain is None
    assert obj.workflow_definition is None


def test_constructor_with_all_existing_fields(valid_data):
    """Test constructor with all currently existing fields."""
    obj = SubWorkflowParams(**valid_data)

    # Verify all fields are set correctly
    assert obj.name == "test_workflow"
    assert obj.version == 1
    assert obj.task_to_domain == {"task1": "domain1", "task2": "domain2"}
    assert obj.workflow_definition == valid_data["workflow_definition"]


def test_constructor_with_partial_fields():
    """Test constructor with subset of existing fields."""
    obj = SubWorkflowParams(name="test", version=2)

    assert obj.name == "test"
    assert obj.version == 2
    assert obj.task_to_domain is None
    assert obj.workflow_definition is None


def test_required_fields_exist():
    """Test that all currently required fields still exist."""
    obj = SubWorkflowParams()

    # Verify all expected attributes exist
    required_attributes = ["name", "version", "task_to_domain", "workflow_definition"]
    for attr in required_attributes:
        assert hasattr(
            obj, attr
        ), f"Required attribute '{attr}' is missing from SubWorkflowParams"


def test_field_types_unchanged(valid_data):
    """Test that existing field types haven't changed."""
    obj = SubWorkflowParams(**valid_data)

    # Test field type expectations based on swagger_types
    assert isinstance(obj.name, str)
    assert isinstance(obj.version, int)
    assert isinstance(obj.task_to_domain, dict)
    # workflow_definition should accept WorkflowDef type (mocked here)
    assert obj.workflow_definition is not None


def test_field_setters_work(mocker):
    """Test that all existing field setters still work."""
    obj = SubWorkflowParams()

    # Test setting each field individually
    obj.name = "new_name"
    assert obj.name == "new_name"

    obj.version = 5
    assert obj.version == 5

    new_task_map = {"new_task": "new_domain"}
    obj.task_to_domain = new_task_map
    assert obj.task_to_domain == new_task_map

    new_workflow_def = mocker.MagicMock()
    obj.workflow_definition = new_workflow_def
    assert obj.workflow_definition == new_workflow_def


def test_field_getters_work(valid_data):
    """Test that all existing field getters still work."""
    obj = SubWorkflowParams(**valid_data)

    # Test getting each field
    assert obj.name == "test_workflow"
    assert obj.version == 1
    assert obj.task_to_domain == {"task1": "domain1", "task2": "domain2"}
    assert obj.workflow_definition == valid_data["workflow_definition"]


def test_none_values_allowed():
    """Test that None values are still allowed for optional fields."""
    obj = SubWorkflowParams()

    # Test setting fields to None
    obj.name = None
    obj.version = None
    obj.task_to_domain = None
    obj.workflow_definition = None

    assert obj.name is None
    assert obj.version is None
    assert obj.task_to_domain is None
    assert obj.workflow_definition is None


def test_swagger_types_unchanged():
    """Test that swagger_types mapping hasn't changed for existing fields."""
    expected_swagger_types = {
        "name": "str",
        "version": "int",
        "task_to_domain": "dict(str, str)",
        "workflow_definition": "WorkflowDef",
    }

    # Verify existing types are preserved
    for field, expected_type in expected_swagger_types.items():
        assert (
            field in SubWorkflowParams.swagger_types
        ), f"Field '{field}' missing from swagger_types"
        assert (
            SubWorkflowParams.swagger_types[field] == expected_type
        ), f"Type for field '{field}' has changed"


def test_attribute_map_unchanged():
    """Test that attribute_map hasn't changed for existing fields."""
    expected_attribute_map = {
        "name": "name",
        "version": "version",
        "task_to_domain": "taskToDomain",
        "workflow_definition": "workflowDefinition",
    }

    # Verify existing mappings are preserved
    for field, expected_json_key in expected_attribute_map.items():
        assert (
            field in SubWorkflowParams.attribute_map
        ), f"Field '{field}' missing from attribute_map"
        assert (
            SubWorkflowParams.attribute_map[field] == expected_json_key
        ), f"JSON mapping for field '{field}' has changed"


def test_to_dict_method_works(valid_data):
    """Test that to_dict method still works with existing fields."""
    obj = SubWorkflowParams(**valid_data)
    result = obj.to_dict()

    assert isinstance(result, dict)
    assert result["name"] == "test_workflow"
    assert result["version"] == 1
    assert result["task_to_domain"] == {"task1": "domain1", "task2": "domain2"}


def test_to_str_method_works(valid_data):
    """Test that to_str method still works."""
    obj = SubWorkflowParams(**valid_data)
    result = obj.to_str()

    assert isinstance(result, str)
    assert "test_workflow" in result


def test_equality_comparison_works(valid_data):
    """Test that equality comparison still works with existing fields."""
    obj1 = SubWorkflowParams(**valid_data)
    obj2 = SubWorkflowParams(**valid_data)
    obj3 = SubWorkflowParams(name="different")

    assert obj1 == obj2
    assert obj1 != obj3
    assert obj1 != "not_a_subworkflow_params"


def test_task_to_domain_dict_structure():
    """Test that task_to_domain maintains expected dict(str, str) structure."""
    obj = SubWorkflowParams()

    # Test valid dict assignment
    valid_dict = {"task1": "domain1", "task2": "domain2"}
    obj.task_to_domain = valid_dict
    assert obj.task_to_domain == valid_dict

    # Test empty dict
    obj.task_to_domain = {}
    assert obj.task_to_domain == {}
