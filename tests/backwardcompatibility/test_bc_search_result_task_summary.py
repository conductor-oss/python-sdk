import pytest

from conductor.client.http.models import SearchResultTaskSummary


@pytest.fixture
def mock_task_summary_1(mocker):
    """Set up test fixture with first mock task summary."""
    mock_summary = mocker.Mock()
    mock_summary.to_dict = mocker.Mock(return_value={"task_id": "task1"})
    return mock_summary


@pytest.fixture
def mock_task_summary_2(mocker):
    """Set up test fixture with second mock task summary."""
    mock_summary = mocker.Mock()
    mock_summary.to_dict = mocker.Mock(return_value={"task_id": "task2"})
    return mock_summary


@pytest.fixture
def sample_results(mock_task_summary_1, mock_task_summary_2):
    """Set up test fixture with sample results."""
    return [mock_task_summary_1, mock_task_summary_2]


def test_class_exists():
    """Test that the SearchResultTaskSummary class exists."""
    assert hasattr(SearchResultTaskSummary, "__init__")
    assert SearchResultTaskSummary.__name__ == "SearchResultTaskSummaryAdapter"


def test_required_class_attributes_exist():
    """Test that required class-level attributes exist and haven't changed."""
    # Verify swagger_types exists and contains expected fields
    assert hasattr(SearchResultTaskSummary, "swagger_types")
    swagger_types = SearchResultTaskSummary.swagger_types

    # These fields must exist (backward compatibility)
    required_fields = {"total_hits": "int", "results": "list[TaskSummary]"}

    for field_name, field_type in required_fields.items():
        assert (
            field_name in swagger_types
        ), f"Field '{field_name}' missing from swagger_types"
        assert (
            swagger_types[field_name] == field_type
        ), f"Field '{field_name}' type changed from '{field_type}' to '{swagger_types[field_name]}'"

    # Verify attribute_map exists and contains expected mappings
    assert hasattr(SearchResultTaskSummary, "attribute_map")
    attribute_map = SearchResultTaskSummary.attribute_map

    required_mappings = {"total_hits": "totalHits", "results": "results"}

    for field_name, json_key in required_mappings.items():
        assert (
            field_name in attribute_map
        ), f"Field '{field_name}' missing from attribute_map"
        assert (
            attribute_map[field_name] == json_key
        ), f"Field '{field_name}' json mapping changed from '{json_key}' to '{attribute_map[field_name]}'"


def test_constructor_signature_compatibility(sample_results):
    """Test that constructor maintains backward compatibility."""
    # Test constructor with no arguments (original behavior)
    obj = SearchResultTaskSummary()
    assert obj is not None
    assert obj.total_hits is None
    assert obj.results is None

    # Test constructor with total_hits only
    obj = SearchResultTaskSummary(total_hits=100)
    assert obj.total_hits == 100
    assert obj.results is None

    # Test constructor with results only
    obj = SearchResultTaskSummary(results=sample_results)
    assert obj.total_hits is None
    assert obj.results == sample_results

    # Test constructor with both parameters
    obj = SearchResultTaskSummary(total_hits=50, results=sample_results)
    assert obj.total_hits == 50
    assert obj.results == sample_results


def test_total_hits_property_compatibility():
    """Test that total_hits property maintains backward compatibility."""
    obj = SearchResultTaskSummary()

    # Test property exists
    assert hasattr(obj, "total_hits")

    # Test getter returns None by default
    assert obj.total_hits is None

    # Test setter accepts int values
    obj.total_hits = 42
    assert obj.total_hits == 42

    # Test setter accepts None
    obj.total_hits = None
    assert obj.total_hits is None

    # Test that private attribute exists
    assert hasattr(obj, "_total_hits")


def test_results_property_compatibility(sample_results):
    """Test that results property maintains backward compatibility."""
    obj = SearchResultTaskSummary()

    # Test property exists
    assert hasattr(obj, "results")

    # Test getter returns None by default
    assert obj.results is None

    # Test setter accepts list values
    obj.results = sample_results
    assert obj.results == sample_results

    # Test setter accepts empty list
    obj.results = []
    assert obj.results == []

    # Test setter accepts None
    obj.results = None
    assert obj.results is None

    # Test that private attribute exists
    assert hasattr(obj, "_results")


def test_instance_attributes_exist():
    """Test that expected instance attributes exist after initialization."""
    obj = SearchResultTaskSummary()

    # Test private attributes exist
    required_private_attrs = ["_total_hits", "_results"]
    for attr in required_private_attrs:
        assert hasattr(obj, attr), f"Required private attribute '{attr}' missing"

    # Test discriminator attribute exists (from swagger pattern)
    assert hasattr(obj, "discriminator")
    assert obj.discriminator is None


def test_required_methods_exist(sample_results):
    """Test that required methods exist and maintain backward compatibility."""
    obj = SearchResultTaskSummary(total_hits=10, results=sample_results)

    required_methods = ["to_dict", "to_str", "__repr__", "__eq__", "__ne__"]

    for method_name in required_methods:
        assert hasattr(obj, method_name), f"Required method '{method_name}' missing"
        assert callable(getattr(obj, method_name)), f"'{method_name}' is not callable"


def test_to_dict_method_compatibility(sample_results):
    """Test that to_dict method maintains expected behavior."""
    obj = SearchResultTaskSummary(total_hits=25, results=sample_results)

    result_dict = obj.to_dict()

    # Test return type
    assert isinstance(result_dict, dict)

    # Test expected keys exist
    expected_keys = ["total_hits", "results"]
    for key in expected_keys:
        assert key in result_dict, f"Expected key '{key}' missing from to_dict() result"

    # Test values
    assert result_dict["total_hits"] == 25
    assert isinstance(result_dict["results"], list)


def test_to_str_method_compatibility():
    """Test that to_str method maintains expected behavior."""
    obj = SearchResultTaskSummary(total_hits=15)

    result_str = obj.to_str()

    # Test return type
    assert isinstance(result_str, str)
    # Test it contains some representation of the data
    assert "total_hits" in result_str


def test_equality_methods_compatibility(sample_results):
    """Test that equality methods maintain expected behavior."""
    obj1 = SearchResultTaskSummary(total_hits=30, results=sample_results)
    obj2 = SearchResultTaskSummary(total_hits=30, results=sample_results)
    obj3 = SearchResultTaskSummary(total_hits=40, results=sample_results)

    # Test __eq__
    assert obj1 == obj2
    assert not (obj1 == obj3)
    assert not (obj1 == "not_an_object")

    # Test __ne__
    assert not (obj1 != obj2)
    assert obj1 != obj3
    assert obj1 != "not_an_object"


def test_field_type_validation_compatibility(mock_task_summary_1, sample_results):
    """Test that field type expectations are maintained."""
    obj = SearchResultTaskSummary()

    # total_hits should accept int-like values (current behavior: no validation)
    # Test that setter doesn't break with various inputs
    test_values = [0, 1, 100, -1]  # Valid int values

    for value in test_values:
        try:
            obj.total_hits = value
            assert obj.total_hits == value
        except Exception as e:  # noqa: PERF203
            pytest.fail(f"Setting total_hits to {value} raised {type(e).__name__}: {e}")

    # results should accept list-like values
    test_lists = [[], [mock_task_summary_1], sample_results]

    for value in test_lists:
        try:
            obj.results = value
            assert obj.results == value
        except Exception as e:  # noqa: PERF203
            pytest.fail(f"Setting results to {value} raised {type(e).__name__}: {e}")


def test_repr_method_compatibility():
    """Test that __repr__ method maintains expected behavior."""
    obj = SearchResultTaskSummary(total_hits=5)

    repr_str = repr(obj)

    # Test return type
    assert isinstance(repr_str, str)
    # Should be same as to_str()
    assert repr_str == obj.to_str()


def test_new_fields_ignored_gracefully():
    """Test that the model can handle new fields being added (forward compatibility)."""
    obj = SearchResultTaskSummary()

    # Test that we can add new attributes without breaking existing functionality
    obj.new_field = "new_value"
    assert obj.new_field == "new_value"

    # Test that existing functionality still works
    obj.total_hits = 100
    assert obj.total_hits == 100

    # Test that to_dict still works (might or might not include new field)
    result_dict = obj.to_dict()
    assert isinstance(result_dict, dict)
