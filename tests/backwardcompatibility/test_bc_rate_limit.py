from conductor.client.http.models import RateLimit


def test_constructor_signature_compatibility():
    """Test that constructor accepts expected parameters and maintains backward compatibility."""
    # Test default constructor (no parameters)
    rate_limit = RateLimit()
    assert rate_limit is not None

    # Test constructor with all original parameters
    rate_limit = RateLimit(tag="test-tag", concurrent_execution_limit=5)
    assert rate_limit.tag == "test-tag"
    assert rate_limit.concurrent_execution_limit == 5

    # Test constructor with partial parameters (original behavior)
    rate_limit = RateLimit(tag="partial-tag")
    assert rate_limit.tag == "partial-tag"
    assert rate_limit.concurrent_execution_limit is None

    rate_limit = RateLimit(concurrent_execution_limit=10)
    assert rate_limit.tag is None
    assert rate_limit.concurrent_execution_limit == 10


def test_required_fields_exist():
    """Test that all original fields still exist and are accessible."""
    rate_limit = RateLimit()

    # Verify original fields exist as properties
    assert hasattr(rate_limit, "tag")
    assert hasattr(rate_limit, "concurrent_execution_limit")

    # Verify properties can be accessed (getter)
    tag_value = rate_limit.tag
    limit_value = rate_limit.concurrent_execution_limit

    # Initial values should be None (original behavior)
    assert tag_value is None
    assert limit_value is None


def test_field_types_unchanged():
    """Test that original field types are preserved."""
    rate_limit = RateLimit()

    # Test string field type
    rate_limit.tag = "test-string"
    assert isinstance(rate_limit.tag, str)

    # Test integer field type
    rate_limit.concurrent_execution_limit = 42
    assert isinstance(rate_limit.concurrent_execution_limit, int)


def test_field_assignment_compatibility():
    """Test that field assignment works as expected (setter functionality)."""
    rate_limit = RateLimit()

    # Test tag assignment
    rate_limit.tag = "assigned-tag"
    assert rate_limit.tag == "assigned-tag"

    # Test concurrent_execution_limit assignment
    rate_limit.concurrent_execution_limit = 100
    assert rate_limit.concurrent_execution_limit == 100

    # Test None assignment (should be allowed)
    rate_limit.tag = None
    assert rate_limit.tag is None

    rate_limit.concurrent_execution_limit = None
    assert rate_limit.concurrent_execution_limit is None


def test_swagger_metadata_compatibility():
    """Test that swagger-related metadata is preserved."""
    # Test swagger_types class attribute exists
    assert hasattr(RateLimit, "swagger_types")
    swagger_types = RateLimit.swagger_types

    # Verify original field type definitions
    assert "tag" in swagger_types
    assert swagger_types["tag"] == "str"

    assert "concurrent_execution_limit" in swagger_types
    assert swagger_types["concurrent_execution_limit"] == "int"

    # Test attribute_map class attribute exists
    assert hasattr(RateLimit, "attribute_map")
    attribute_map = RateLimit.attribute_map

    # Verify original attribute mappings
    assert "tag" in attribute_map
    assert attribute_map["tag"] == "tag"

    assert "concurrent_execution_limit" in attribute_map
    assert attribute_map["concurrent_execution_limit"] == "concurrentExecutionLimit"


def test_internal_attributes_exist():
    """Test that internal attributes are properly initialized."""
    rate_limit = RateLimit()

    # Verify internal private attributes exist (original implementation detail)
    assert hasattr(rate_limit, "_tag")
    assert hasattr(rate_limit, "_concurrent_execution_limit")
    assert hasattr(rate_limit, "discriminator")

    # Initial state should match original behavior
    assert rate_limit._tag is None
    assert rate_limit._concurrent_execution_limit is None
    assert rate_limit.discriminator is None


def test_to_dict_method_compatibility():
    """Test that to_dict method works and produces expected structure."""
    rate_limit = RateLimit(tag="dict-tag", concurrent_execution_limit=25)

    # Method should exist
    assert hasattr(rate_limit, "to_dict")
    assert callable(rate_limit.to_dict)

    # Should return a dictionary
    result = rate_limit.to_dict()
    assert isinstance(result, dict)

    # Should contain original fields with correct values
    assert "tag" in result
    assert result["tag"] == "dict-tag"

    assert "concurrent_execution_limit" in result
    assert result["concurrent_execution_limit"] == 25


def test_to_str_method_compatibility():
    """Test that to_str method exists and works."""
    rate_limit = RateLimit(tag="str-tag", concurrent_execution_limit=15)

    # Method should exist
    assert hasattr(rate_limit, "to_str")
    assert callable(rate_limit.to_str)

    # Should return a string
    result = rate_limit.to_str()
    assert isinstance(result, str)

    # Should contain field values
    assert "str-tag" in result
    assert "15" in result


def test_repr_method_compatibility():
    """Test that __repr__ method works."""
    rate_limit = RateLimit(tag="repr-tag", concurrent_execution_limit=30)

    # Should be able to get string representation
    repr_str = repr(rate_limit)
    assert isinstance(repr_str, str)

    # Should contain field values
    assert "repr-tag" in repr_str
    assert "30" in repr_str


def test_equality_methods_compatibility():
    """Test that equality comparison methods work."""
    rate_limit1 = RateLimit(tag="equal-tag", concurrent_execution_limit=50)
    rate_limit2 = RateLimit(tag="equal-tag", concurrent_execution_limit=50)
    rate_limit3 = RateLimit(tag="different-tag", concurrent_execution_limit=50)

    # Test equality
    assert rate_limit1 == rate_limit2
    assert not (rate_limit1 == rate_limit3)

    # Test inequality
    assert not (rate_limit1 != rate_limit2)
    assert rate_limit1 != rate_limit3

    # Test inequality with different types
    assert not (rate_limit1 == "not-a-rate-limit")
    assert rate_limit1 != "not-a-rate-limit"


def test_field_modification_after_construction():
    """Test that fields can be modified after object construction."""
    rate_limit = RateLimit(tag="initial-tag", concurrent_execution_limit=1)

    # Modify fields
    rate_limit.tag = "modified-tag"
    rate_limit.concurrent_execution_limit = 99

    # Verify modifications
    assert rate_limit.tag == "modified-tag"
    assert rate_limit.concurrent_execution_limit == 99

    # Verify to_dict reflects changes
    result_dict = rate_limit.to_dict()
    assert result_dict["tag"] == "modified-tag"
    assert result_dict["concurrent_execution_limit"] == 99


def test_none_values_handling():
    """Test that None values are handled properly (original behavior)."""
    # Constructor with None values
    rate_limit = RateLimit(tag=None, concurrent_execution_limit=None)
    assert rate_limit.tag is None
    assert rate_limit.concurrent_execution_limit is None

    # Assignment of None values
    rate_limit = RateLimit(tag="some-tag", concurrent_execution_limit=10)
    rate_limit.tag = None
    rate_limit.concurrent_execution_limit = None

    assert rate_limit.tag is None
    assert rate_limit.concurrent_execution_limit is None

    # to_dict with None values
    result_dict = rate_limit.to_dict()
    assert result_dict["tag"] is None
    assert result_dict["concurrent_execution_limit"] is None
