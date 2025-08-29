import pytest

from conductor.client.http.models.search_result_task import SearchResultTask


@pytest.fixture
def mock_task1(mocker):
    """Set up test fixture with first mock task."""
    mock_task = mocker.MagicMock()
    mock_task.to_dict.return_value = {"id": "task1", "name": "Test Task 1"}
    return mock_task


@pytest.fixture
def mock_task2(mocker):
    """Set up test fixture with second mock task."""
    mock_task = mocker.MagicMock()
    mock_task.to_dict.return_value = {"id": "task2", "name": "Test Task 2"}
    return mock_task


@pytest.fixture
def mock_tasks(mock_task1, mock_task2):
    """Set up test fixture with list of mock tasks."""
    return [mock_task1, mock_task2]


def test_class_exists_and_importable():
    """Verify the SearchResultTask class exists and can be imported."""
    assert hasattr(SearchResultTask, "__init__")
    assert callable(SearchResultTask)


def test_constructor_signature_compatibility(mock_tasks):
    """Verify constructor accepts expected parameters with defaults."""
    # Should work with no arguments (all defaults)
    obj = SearchResultTask()
    assert obj is not None

    # Should work with positional arguments
    obj = SearchResultTask(100, mock_tasks)
    assert obj is not None

    # Should work with keyword arguments
    obj = SearchResultTask(total_hits=100, results=mock_tasks)
    assert obj is not None

    # Should work with mixed arguments
    obj = SearchResultTask(100, results=mock_tasks)
    assert obj is not None


def test_required_attributes_exist():
    """Verify all expected attributes exist in the class."""
    # Class-level attributes
    assert hasattr(SearchResultTask, "swagger_types")
    assert hasattr(SearchResultTask, "attribute_map")

    # Instance attributes after initialization
    obj = SearchResultTask()
    assert hasattr(obj, "_total_hits")
    assert hasattr(obj, "_results")
    assert hasattr(obj, "discriminator")


def test_swagger_types_structure():
    """Verify swagger_types dictionary contains expected field type mappings."""
    expected_types = {"total_hits": "int", "results": "list[Task]"}

    assert SearchResultTask.swagger_types == expected_types

    # Verify types haven't changed
    for field, expected_type in expected_types.items():
        assert field in SearchResultTask.swagger_types
        assert SearchResultTask.swagger_types[field] == expected_type


def test_attribute_map_structure():
    """Verify attribute_map dictionary contains expected field name mappings."""
    expected_map = {"total_hits": "totalHits", "results": "results"}

    assert SearchResultTask.attribute_map == expected_map

    # Verify mappings haven't changed
    for field, expected_mapping in expected_map.items():
        assert field in SearchResultTask.attribute_map
        assert SearchResultTask.attribute_map[field] == expected_mapping


def test_total_hits_property_compatibility():
    """Verify total_hits property getter/setter behavior."""
    obj = SearchResultTask()

    # Verify property exists
    assert hasattr(obj, "total_hits")

    # Test getter returns None by default
    assert obj.total_hits is None

    # Test setter accepts int values
    obj.total_hits = 100
    assert obj.total_hits == 100

    # Test setter accepts None
    obj.total_hits = None
    assert obj.total_hits is None

    # Verify private attribute is set correctly
    obj.total_hits = 50
    assert obj._total_hits == 50


def test_results_property_compatibility(mock_tasks):
    """Verify results property getter/setter behavior."""
    obj = SearchResultTask()

    # Verify property exists
    assert hasattr(obj, "results")

    # Test getter returns None by default
    assert obj.results is None

    # Test setter accepts list values
    obj.results = mock_tasks
    assert obj.results == mock_tasks

    # Test setter accepts None
    obj.results = None
    assert obj.results is None

    # Test setter accepts empty list
    obj.results = []
    assert obj.results == []

    # Verify private attribute is set correctly
    obj.results = mock_tasks
    assert obj._results == mock_tasks


def test_constructor_parameter_assignment(mock_tasks):
    """Verify constructor properly assigns parameters to properties."""
    obj = SearchResultTask(total_hits=200, results=mock_tasks)

    assert obj.total_hits == 200
    assert obj.results == mock_tasks
    assert obj._total_hits == 200
    assert obj._results == mock_tasks


def test_discriminator_attribute():
    """Verify discriminator attribute exists and is initialized."""
    obj = SearchResultTask()
    assert hasattr(obj, "discriminator")
    assert obj.discriminator is None


def test_to_dict_method_compatibility(mock_tasks):
    """Verify to_dict method exists and returns expected structure."""
    obj = SearchResultTask(total_hits=100, results=mock_tasks)

    # Method should exist
    assert hasattr(obj, "to_dict")
    assert callable(obj.to_dict)

    # Should return a dict
    result = obj.to_dict()
    assert isinstance(result, dict)

    # Should contain expected keys
    assert "total_hits" in result
    assert "results" in result

    # Should have correct values
    assert result["total_hits"] == 100


def test_to_str_method_compatibility(mock_tasks):
    """Verify to_str method exists and returns string."""
    obj = SearchResultTask(total_hits=100, results=mock_tasks)

    assert hasattr(obj, "to_str")
    assert callable(obj.to_str)

    result = obj.to_str()
    assert isinstance(result, str)


def test_repr_method_compatibility(mock_tasks):
    """Verify __repr__ method exists and returns string."""
    obj = SearchResultTask(total_hits=100, results=mock_tasks)

    result = repr(obj)
    assert isinstance(result, str)


def test_equality_methods_compatibility(mock_tasks):
    """Verify __eq__ and __ne__ methods work correctly."""
    obj1 = SearchResultTask(total_hits=100, results=mock_tasks)
    obj2 = SearchResultTask(total_hits=100, results=mock_tasks)
    obj3 = SearchResultTask(total_hits=200, results=mock_tasks)

    # Test equality
    assert obj1 == obj2
    assert obj1 != obj3

    # Test inequality with different types
    assert obj1 != "not_a_search_result"
    assert obj1 is not None


def test_backward_compatibility_with_none_values():
    """Verify model handles None values correctly (important for backward compatibility)."""
    # Constructor with None values
    obj = SearchResultTask(total_hits=None, results=None)
    assert obj.total_hits is None
    assert obj.results is None

    # Property assignment with None
    obj = SearchResultTask()
    obj.total_hits = None
    obj.results = None
    assert obj.total_hits is None
    assert obj.results is None


def test_to_dict_with_none_values():
    """Verify to_dict handles None values correctly."""
    obj = SearchResultTask(total_hits=None, results=None)
    result = obj.to_dict()

    assert isinstance(result, dict)
    assert "total_hits" in result
    assert "results" in result
    assert result["total_hits"] is None
    assert result["results"] is None


def test_field_types_not_changed(mock_tasks):
    """Verify that existing field types haven't been modified."""
    # This test ensures that if someone changes field types,
    # the backward compatibility is broken and test will fail

    obj = SearchResultTask()

    # total_hits should accept int or None
    obj.total_hits = 100
    assert isinstance(obj.total_hits, int)

    obj.total_hits = None
    assert obj.total_hits is None

    # results should accept list or None
    obj.results = []
    assert isinstance(obj.results, list)

    obj.results = mock_tasks
    assert isinstance(obj.results, list)

    obj.results = None
    assert obj.results is None
