from conductor.client.adapters.models.external_storage_location_adapter import (
    ExternalStorageLocationAdapter,
)


def test_constructor_with_no_arguments():
    """Test that constructor works without any arguments (current behavior)."""
    storage_location = ExternalStorageLocationAdapter()
    assert storage_location is not None
    assert storage_location.uri is None
    assert storage_location.path is None


def test_constructor_with_all_arguments():
    """Test constructor with all known arguments."""
    uri = "s3://my-bucket"
    path = "/data/files"
    storage_location = ExternalStorageLocationAdapter(uri=uri, path=path)
    assert storage_location.uri == uri
    assert storage_location.path == path


def test_constructor_with_partial_arguments():
    """Test constructor with partial arguments."""
    # Test with only uri
    storage_location1 = ExternalStorageLocationAdapter(uri="s3://bucket1")
    assert storage_location1.uri == "s3://bucket1"
    assert storage_location1.path is None
    # Test with only path
    storage_location2 = ExternalStorageLocationAdapter(path="/data")
    assert storage_location2.uri is None
    assert storage_location2.path == "/data"


def test_required_fields_exist():
    """Test that all expected fields exist in the model."""
    storage_location = ExternalStorageLocationAdapter()
    # These fields must exist for backward compatibility
    required_attributes = ["uri", "path"]
    for attr in required_attributes:
        assert hasattr(
            storage_location, attr
        ), f"Required attribute '{attr}' is missing"


def test_field_types_unchanged():
    """Test that field types haven't changed."""
    # Verify swagger_types mapping exists and contains expected types
    assert hasattr(ExternalStorageLocationAdapter, "swagger_types")
    expected_types = {"uri": "str", "path": "str"}
    for field, expected_type in expected_types.items():
        assert (
            field in ExternalStorageLocationAdapter.swagger_types
        ), f"Field '{field}' missing from swagger_types"

        assert ExternalStorageLocationAdapter.swagger_types[field] == expected_type, (
            f"Field '{field}' type changed from '{expected_type}' to "
            f"'{ExternalStorageLocationAdapter.swagger_types[field]}'"
        )


def test_attribute_map_unchanged():
    """Test that attribute mapping hasn't changed."""
    assert hasattr(ExternalStorageLocationAdapter, "attribute_map")
    expected_mapping = {"uri": "uri", "path": "path"}
    for attr, json_key in expected_mapping.items():
        assert (
            attr in ExternalStorageLocationAdapter.attribute_map
        ), f"Attribute '{attr}' missing from attribute_map"

        assert (
            ExternalStorageLocationAdapter.attribute_map[attr] == json_key
        ), f"Attribute mapping for '{attr}' changed"


def test_uri_property_behavior():
    """Test uri property getter and setter behavior."""
    storage_location = ExternalStorageLocationAdapter()
    # Test getter when value is None
    assert storage_location.uri is None
    # Test setter with string value
    test_uri = "s3://test-bucket/path"
    storage_location.uri = test_uri
    assert storage_location.uri == test_uri
    # Test setter with None
    storage_location.uri = None
    assert storage_location.uri is None


def test_path_property_behavior():
    """Test path property getter and setter behavior."""
    storage_location = ExternalStorageLocationAdapter()
    # Test getter when value is None
    assert storage_location.path is None
    # Test setter with string value
    test_path = "/data/files/input"
    storage_location.path = test_path
    assert storage_location.path == test_path
    # Test setter with None
    storage_location.path = None
    assert storage_location.path is None


def test_to_dict_method_exists_and_works():
    """Test that to_dict method exists and produces expected output."""
    storage_location = ExternalStorageLocationAdapter(uri="s3://bucket", path="/data")
    result = storage_location.to_dict()
    assert isinstance(result, dict)
    # Verify expected keys exist in output
    expected_keys = ["uri", "path"]
    for key in expected_keys:
        assert key in result
    assert result["uri"] == "s3://bucket"
    assert result["path"] == "/data"


def test_to_str_method_exists():
    """Test that to_str method exists and returns string."""
    storage_location = ExternalStorageLocationAdapter()
    result = storage_location.to_str()
    assert isinstance(result, str)


def test_repr_method_exists():
    """Test that __repr__ method exists and returns string."""
    storage_location = ExternalStorageLocationAdapter()
    result = repr(storage_location)
    assert isinstance(result, str)


def test_equality_methods_exist():
    """Test that equality methods exist and work correctly."""
    storage1 = ExternalStorageLocationAdapter(uri="s3://bucket", path="/data")
    storage2 = ExternalStorageLocationAdapter(uri="s3://bucket", path="/data")
    storage3 = ExternalStorageLocationAdapter(uri="s3://other", path="/data")
    # Test __eq__
    assert storage1 == storage2
    assert storage1 != storage3
    # Test __ne__
    assert not (storage1 != storage2)
    assert storage1 != storage3
    # Test equality with non-ExternalStorageLocationAdapter object
    assert storage1 != "not_a_storage_location"


def test_private_attributes_exist():
    """Test that private attributes exist (implementation detail preservation)."""
    storage_location = ExternalStorageLocationAdapter()
    # These private attributes should exist for backward compatibility
    assert hasattr(storage_location, "_uri")
    assert hasattr(storage_location, "_path")
    assert hasattr(storage_location, "discriminator")


def test_string_type_validation():
    """Test that string fields accept string values without validation errors."""
    storage_location = ExternalStorageLocationAdapter()
    # Test various string values
    string_values = [
        "",  # empty string
        "simple_string",
        "s3://bucket/path/to/file",
        "/absolute/path",
        "relative/path",
        "string with spaces",
        "string-with-dashes",
        "string_with_underscores",
        "http://example.com/path?query=value",
    ]
    for value in string_values:
        # Should not raise any exceptions
        storage_location.uri = value
        assert storage_location.uri == value
        storage_location.path = value
        assert storage_location.path == value


def test_none_values_accepted():
    """Test that None values are accepted (current behavior)."""
    storage_location = ExternalStorageLocationAdapter()
    # Set to None should work
    storage_location.uri = None
    storage_location.path = None
    assert storage_location.uri is None
    assert storage_location.path is None


def test_field_independence():
    """Test that fields can be set independently."""
    storage_location = ExternalStorageLocationAdapter()
    # Set uri only
    storage_location.uri = "s3://bucket"
    assert storage_location.uri == "s3://bucket"
    assert storage_location.path is None
    # Set path only (clear uri first)
    storage_location.uri = None
    storage_location.path = "/data"
    assert storage_location.uri is None
    assert storage_location.path == "/data"
    # Set both
    storage_location.uri = "s3://bucket"
    storage_location.path = "/data"
    assert storage_location.uri == "s3://bucket"
    assert storage_location.path == "/data"
