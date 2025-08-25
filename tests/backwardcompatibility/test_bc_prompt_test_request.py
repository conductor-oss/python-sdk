import pytest


from conductor.client.adapters.models.prompt_template_test_request_adapter import (
    PromptTemplateTestRequestAdapter,
)


@pytest.fixture
def valid_data():
    """Set up test fixture with known valid data."""
    return {
        "llm_provider": "openai",
        "model": "gpt-4",
        "prompt": "Test prompt",
        "prompt_variables": {"var1": "value1", "var2": 42},
        "stop_words": ["stop1", "stop2"],
        "temperature": 0.7,
        "top_p": 0.9,
    }


def test_class_exists():
    """Verify the class still exists and is importable."""
    assert PromptTemplateTestRequestAdapter is not None
    assert callable(PromptTemplateTestRequestAdapter)
    assert PromptTemplateTestRequestAdapter.__name__ == "PromptTemplateTestRequestAdapter"


def test_constructor_signature_backward_compatible():
    """Verify constructor accepts all existing parameters with defaults."""
    # Should work with no parameters (all defaults)
    obj = PromptTemplateTestRequestAdapter()
    assert isinstance(obj, PromptTemplateTestRequestAdapter)

    # Should work with all original parameters
    obj = PromptTemplateTestRequestAdapter(
        llm_provider="openai",
        model="gpt-4",
        prompt="test",
        prompt_variables={"key": "value"},
        stop_words=["stop"],
        temperature=0.5,
        top_p=0.8,
    )
    assert isinstance(obj, PromptTemplateTestRequestAdapter)


def test_all_existing_properties_exist():
    """Verify all known properties still exist."""
    obj = PromptTemplateTestRequestAdapter()

    # Test property existence
    expected_properties = [
        "llm_provider",
        "model",
        "prompt",
        "prompt_variables",
        "stop_words",
        "temperature",
        "top_p",
    ]

    for prop in expected_properties:
        assert hasattr(obj, prop), f"Property '{prop}' missing"
        # Verify property is readable
        getattr(obj, prop)
        # Should not raise exception


def test_property_getters_return_correct_types(valid_data):
    """Verify property getters return expected types."""
    obj = PromptTemplateTestRequestAdapter(**valid_data)

    # Test each property returns expected type
    type_checks = [
        ("llm_provider", str),
        ("model", str),
        ("prompt", str),
        ("prompt_variables", dict),
        ("stop_words", list),
        ("temperature", (int, float)),  # Allow both int and float
        ("top_p", (int, float)),
    ]

    for prop_name, expected_type in type_checks:
        value = getattr(obj, prop_name)
        assert isinstance(
            value, expected_type
        ), f"Property '{prop_name}' should be {expected_type}, got {type(value)}"


def test_property_setters_work():
    """Verify all property setters still work."""
    obj = PromptTemplateTestRequestAdapter()

    # Test setting each property
    test_values = {
        "llm_provider": "anthropic",
        "model": "claude-3",
        "prompt": "New prompt",
        "prompt_variables": {"new_key": "new_value"},
        "stop_words": ["new_stop"],
        "temperature": 0.3,
        "top_p": 0.95,
    }

    for prop_name, test_value in test_values.items():
        setattr(obj, prop_name, test_value)
        retrieved_value = getattr(obj, prop_name)
        assert (
            retrieved_value == test_value
        ), f"Property '{prop_name}' setter/getter failed"


def test_swagger_types_dict_exists():
    """Verify swagger_types dict still exists with expected structure."""
    assert hasattr(PromptTemplateTestRequestAdapter, "swagger_types")
    swagger_types = PromptTemplateTestRequestAdapter.swagger_types
    assert isinstance(swagger_types, dict)

    # Verify all expected fields are present with correct types
    expected_swagger_types = {
        "llm_provider": "str",
        "model": "str",
        "prompt": "str",
        "prompt_variables": "dict(str, object)",
        "stop_words": "list[str]",
        "temperature": "float",
        "top_p": "float",
    }

    for field, expected_type in expected_swagger_types.items():
        assert field in swagger_types, f"Field '{field}' missing from swagger_types"
        assert (
            swagger_types[field] == expected_type
        ), f"Field '{field}' type changed from '{expected_type}' to '{swagger_types[field]}'"


def test_attribute_map_dict_exists():
    """Verify attribute_map dict still exists with expected structure."""
    assert hasattr(PromptTemplateTestRequestAdapter, "attribute_map")
    attribute_map = PromptTemplateTestRequestAdapter.attribute_map
    assert isinstance(attribute_map, dict)

    # Verify all expected mappings are present
    expected_attribute_map = {
        "llm_provider": "llmProvider",
        "model": "model",
        "prompt": "prompt",
        "prompt_variables": "promptVariables",
        "stop_words": "stopWords",
        "temperature": "temperature",
        "top_p": "topP",
    }

    for field, expected_json_key in expected_attribute_map.items():
        assert field in attribute_map, f"Field '{field}' missing from attribute_map"
        assert (
            attribute_map[field] == expected_json_key
        ), f"Field '{field}' JSON mapping changed from '{expected_json_key}' to '{attribute_map[field]}'"


def test_to_dict_method_exists_and_works(valid_data):
    """Verify to_dict method still exists and returns expected structure."""
    obj = PromptTemplateTestRequestAdapter(**valid_data)

    assert hasattr(obj, "to_dict")
    assert callable(obj.to_dict)

    result = obj.to_dict()
    assert isinstance(result, dict)

    # Verify all expected fields are in the result
    expected_fields = [
        "llm_provider",
        "model",
        "prompt",
        "prompt_variables",
        "stop_words",
        "temperature",
        "top_p",
    ]

    for field in expected_fields:
        assert field in result, f"Field '{field}' missing from to_dict() result"


def test_to_str_method_exists_and_works(valid_data):
    """Verify to_str method still exists and returns string."""
    obj = PromptTemplateTestRequestAdapter(**valid_data)

    assert hasattr(obj, "to_str")
    assert callable(obj.to_str)

    result = obj.to_str()
    assert isinstance(result, str)
    assert len(result) > 0


def test_repr_method_exists_and_works(valid_data):
    """Verify __repr__ method still works."""
    obj = PromptTemplateTestRequestAdapter(**valid_data)

    result = repr(obj)
    assert isinstance(result, str)
    assert len(result) > 0


def test_equality_methods_exist_and_work(valid_data):
    """Verify __eq__ and __ne__ methods still work."""
    obj1 = PromptTemplateTestRequestAdapter(**valid_data)
    obj2 = PromptTemplateTestRequestAdapter(**valid_data)
    obj3 = PromptTemplateTestRequestAdapter(llm_provider="different")

    # Test equality
    assert hasattr(obj1, "__eq__")
    assert obj1 == obj2
    assert obj1 != obj3
    assert obj1 != "not an object"

    # Test inequality
    assert hasattr(obj1, "__ne__")
    assert not (obj1 != obj2)
    assert obj1 != obj3


def test_none_values_handling():
    """Verify None values are handled correctly (existing behavior)."""
    obj = PromptTemplateTestRequestAdapter()

    # All properties should be None by default
    expected_none_properties = [
        "llm_provider",
        "model",
        "prompt",
        "prompt_variables",
        "stop_words",
        "temperature",
        "top_p",
    ]

    for prop in expected_none_properties:
        value = getattr(obj, prop)
        assert value is None, f"Property '{prop}' should default to None"


def test_discriminator_attribute_exists():
    """Verify discriminator attribute still exists."""
    obj = PromptTemplateTestRequestAdapter()
    assert hasattr(obj, "discriminator")
    assert obj.discriminator is None  # Should be None by default


def test_private_attributes_exist():
    """Verify private attributes still exist (internal structure)."""
    obj = PromptTemplateTestRequestAdapter()

    expected_private_attrs = [
        "_llm_provider",
        "_model",
        "_prompt",
        "_prompt_variables",
        "_stop_words",
        "_temperature",
        "_top_p",
    ]

    for attr in expected_private_attrs:
        assert hasattr(obj, attr), f"Private attribute '{attr}' missing"


def test_field_type_validation_constraints():
    """Test that existing type constraints are preserved."""
    obj = PromptTemplateTestRequestAdapter()

    # Test string fields accept strings
    string_fields = ["llm_provider", "model", "prompt"]
    for field in string_fields:
        setattr(obj, field, "test_string")
        assert getattr(obj, field) == "test_string"

    # Test dict field accepts dict
    obj.prompt_variables = {"key": "value"}
    assert obj.prompt_variables == {"key": "value"}

    # Test list field accepts list
    obj.stop_words = ["word1", "word2"]
    assert obj.stop_words == ["word1", "word2"]

    # Test numeric fields accept numbers
    obj.temperature = 0.5
    assert obj.temperature == 0.5

    obj.top_p = 0.9
    assert obj.top_p == 0.9


def test_constructor_parameter_order_preserved():
    """Verify constructor parameter order hasn't changed."""
    # This test ensures positional arguments still work
    obj = PromptTemplateTestRequestAdapter(
        "openai",  # llm_provider
        "gpt-4",  # model
        "test prompt",  # prompt
        {"var": "val"},  # prompt_variables
        ["stop"],  # stop_words
        0.7,  # temperature
        0.9,  # top_p
    )

    assert obj.llm_provider == "openai"
    assert obj.model == "gpt-4"
    assert obj.prompt == "test prompt"
    assert obj.prompt_variables == {"var": "val"}
    assert obj.stop_words == ["stop"]
    assert obj.temperature == 0.7
    assert obj.top_p == 0.9
