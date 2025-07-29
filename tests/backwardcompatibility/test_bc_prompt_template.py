import pytest

from conductor.client.http.models.prompt_template import PromptTemplate


@pytest.fixture
def mock_tag(mocker):
    """Set up test fixture with mock tag."""
    mock_tag = mocker.Mock()
    mock_tag.to_dict.return_value = {"name": "test_tag"}
    return mock_tag


@pytest.fixture
def valid_data(mock_tag):
    """Set up test fixture with valid data for all known fields."""
    return {
        "created_by": "test_user",
        "created_on": 1234567890,
        "description": "Test description",
        "integrations": ["integration1", "integration2"],
        "name": "test_template",
        "tags": [mock_tag],
        "template": "Hello {{variable}}",
        "updated_by": "update_user",
        "updated_on": 1234567899,
        "variables": ["variable1", "variable2"],
    }


def test_constructor_with_no_parameters():
    """Test that constructor works with no parameters (all optional)."""
    template = PromptTemplate()
    assert isinstance(template, PromptTemplate)

    # All fields should be None initially
    assert template.created_by is None
    assert template.created_on is None
    assert template.description is None
    assert template.integrations is None
    assert template.name is None
    assert template.tags is None
    assert template.template is None
    assert template.updated_by is None
    assert template.updated_on is None
    assert template.variables is None


def test_constructor_with_all_parameters(valid_data):
    """Test constructor with all known parameters."""
    template = PromptTemplate(**valid_data)

    # Verify all fields are set correctly
    assert template.created_by == "test_user"
    assert template.created_on == 1234567890
    assert template.description == "Test description"
    assert template.integrations == ["integration1", "integration2"]
    assert template.name == "test_template"
    assert template.tags == [valid_data["tags"][0]]  # mock_tag
    assert template.template == "Hello {{variable}}"
    assert template.updated_by == "update_user"
    assert template.updated_on == 1234567899
    assert template.variables == ["variable1", "variable2"]


def test_field_existence_and_accessibility():
    """Test that all expected fields exist and are accessible."""
    template = PromptTemplate()

    # Test property getters exist
    expected_fields = [
        "created_by",
        "created_on",
        "description",
        "integrations",
        "name",
        "tags",
        "template",
        "updated_by",
        "updated_on",
        "variables",
    ]

    for field in expected_fields:
        # Property should exist and be accessible
        assert hasattr(template, field)
        # Should be able to get the value (even if None)
        getattr(template, field)


def test_field_types_remain_consistent(valid_data):
    """Test that field types haven't changed."""
    template = PromptTemplate(**valid_data)

    # Test string fields
    string_fields = ["created_by", "description", "name", "template", "updated_by"]
    for field in string_fields:
        value = getattr(template, field)
        assert isinstance(value, str)

    # Test integer fields
    int_fields = ["created_on", "updated_on"]
    for field in int_fields:
        value = getattr(template, field)
        assert isinstance(value, int)

    # Test list fields
    list_fields = ["integrations", "tags", "variables"]
    for field in list_fields:
        value = getattr(template, field)
        assert isinstance(value, list)


def test_setters_work_correctly(mock_tag):
    """Test that all setters work as expected."""
    template = PromptTemplate()

    # Test setting string fields
    template.created_by = "new_user"
    assert template.created_by == "new_user"

    template.description = "new description"
    assert template.description == "new description"

    template.name = "new_name"
    assert template.name == "new_name"

    template.template = "new template"
    assert template.template == "new template"

    template.updated_by = "new_updater"
    assert template.updated_by == "new_updater"

    # Test setting integer fields
    template.created_on = 9999999999
    assert template.created_on == 9999999999

    template.updated_on = 8888888888
    assert template.updated_on == 8888888888

    # Test setting list fields
    template.integrations = ["new_integration"]
    assert template.integrations == ["new_integration"]

    template.variables = ["new_var"]
    assert template.variables == ["new_var"]

    template.tags = [mock_tag]
    assert template.tags == [mock_tag]


def test_none_values_allowed(valid_data):
    """Test that None values are allowed for all fields."""
    template = PromptTemplate(**valid_data)

    # All fields should accept None
    fields = [
        "created_by",
        "created_on",
        "description",
        "integrations",
        "name",
        "tags",
        "template",
        "updated_by",
        "updated_on",
        "variables",
    ]

    for field in fields:
        setattr(template, field, None)
        assert getattr(template, field) is None


def test_to_dict_method_exists_and_works(valid_data):
    """Test that to_dict method exists and includes all expected fields."""
    template = PromptTemplate(**valid_data)
    result = template.to_dict()

    assert isinstance(result, dict)

    # Check that all expected keys are present
    expected_keys = [
        "created_by",
        "created_on",
        "description",
        "integrations",
        "name",
        "tags",
        "template",
        "updated_by",
        "updated_on",
        "variables",
    ]

    for key in expected_keys:
        assert key in result


def test_to_str_method_exists(valid_data):
    """Test that to_str method exists and returns string."""
    template = PromptTemplate(**valid_data)
    result = template.to_str()
    assert isinstance(result, str)


def test_repr_method_exists(valid_data):
    """Test that __repr__ method exists and returns string."""
    template = PromptTemplate(**valid_data)
    result = repr(template)
    assert isinstance(result, str)


def test_equality_comparison_works(valid_data):
    """Test that equality comparison works correctly."""
    template1 = PromptTemplate(**valid_data)
    template2 = PromptTemplate(**valid_data)
    template3 = PromptTemplate(name="different")

    # Equal objects
    assert template1 == template2
    assert not (template1 != template2)

    # Different objects
    assert template1 != template3
    assert template1 != template3

    # Different type
    assert template1 != "not a template"


def test_swagger_types_attribute_exists():
    """Test that swagger_types class attribute exists and has expected structure."""
    assert hasattr(PromptTemplate, "swagger_types")
    swagger_types = PromptTemplate.swagger_types
    assert isinstance(swagger_types, dict)

    # Check for expected field types
    expected_swagger_types = {
        "created_by": "str",
        "created_on": "int",
        "description": "str",
        "integrations": "list[str]",
        "name": "str",
        "tags": "list[TagObject]",
        "template": "str",
        "updated_by": "str",
        "updated_on": "int",
        "variables": "list[str]",
    }

    for field, expected_type in expected_swagger_types.items():
        assert field in swagger_types
        assert swagger_types[field] == expected_type


def test_attribute_map_exists():
    """Test that attribute_map class attribute exists and has expected structure."""
    assert hasattr(PromptTemplate, "attribute_map")
    attribute_map = PromptTemplate.attribute_map
    assert isinstance(attribute_map, dict)

    # Check for expected attribute mappings
    expected_mappings = {
        "created_by": "createdBy",
        "created_on": "createdOn",
        "description": "description",
        "integrations": "integrations",
        "name": "name",
        "tags": "tags",
        "template": "template",
        "updated_by": "updatedBy",
        "updated_on": "updatedOn",
        "variables": "variables",
    }

    for field, expected_mapping in expected_mappings.items():
        assert field in attribute_map
        assert attribute_map[field] == expected_mapping


def test_discriminator_attribute_exists():
    """Test that discriminator attribute exists and is None."""
    template = PromptTemplate()
    assert hasattr(template, "discriminator")
    assert template.discriminator is None


def test_partial_initialization():
    """Test that partial initialization works (only some fields provided)."""
    partial_data = {
        "name": "partial_template",
        "description": "partial description",
    }

    template = PromptTemplate(**partial_data)

    # Specified fields should be set
    assert template.name == "partial_template"
    assert template.description == "partial description"

    # Other fields should be None
    assert template.created_by is None
    assert template.integrations is None
    assert template.template is None


def test_list_field_mutation_safety():
    """Test that list fields can be safely modified."""
    template = PromptTemplate()

    # Test integrations list
    template.integrations = ["int1"]
    template.integrations.append("int2")
    assert template.integrations == ["int1", "int2"]

    # Test variables list
    template.variables = ["var1"]
    template.variables.extend(["var2", "var3"])
    assert template.variables == ["var1", "var2", "var3"]
