import pytest

from conductor.client.http.models import ScrollableSearchResultWorkflowSummary


@pytest.fixture
def mock_workflow_summary(mocker):
    """Set up test fixture with mock workflow summary."""
    mock_summary = mocker.Mock()
    mock_summary.to_dict = mocker.Mock(return_value={"id": "test"})
    return mock_summary


def test_constructor_signature_backward_compatibility(mock_workflow_summary):
    """Test that constructor signature remains backward compatible."""
    # Should work with no arguments (original behavior)
    obj = ScrollableSearchResultWorkflowSummary()
    assert obj is not None

    # Should work with original parameters
    obj = ScrollableSearchResultWorkflowSummary(
        results=[mock_workflow_summary], query_id="test_query"
    )
    assert obj is not None

    # Should work with keyword arguments (original behavior)
    obj = ScrollableSearchResultWorkflowSummary(results=None, query_id=None)
    assert obj is not None


def test_required_attributes_exist():
    """Test that all originally required attributes still exist."""
    obj = ScrollableSearchResultWorkflowSummary()

    # Core attributes must exist
    assert hasattr(obj, "results")
    assert hasattr(obj, "query_id")

    # Internal attributes must exist
    assert hasattr(obj, "_results")
    assert hasattr(obj, "_query_id")
    assert hasattr(obj, "discriminator")


def test_swagger_metadata_backward_compatibility():
    """Test that swagger metadata remains backward compatible."""
    # swagger_types must contain original fields
    required_swagger_types = {"results": "list[WorkflowSummary]", "query_id": "str"}

    for field, field_type in required_swagger_types.items():
        assert field in ScrollableSearchResultWorkflowSummary.swagger_types
        assert (
            ScrollableSearchResultWorkflowSummary.swagger_types[field] == field_type
        ), f"Type for field '{field}' changed from '{field_type}'"

    # attribute_map must contain original mappings
    required_attribute_map = {"results": "results", "query_id": "queryId"}

    for attr, json_key in required_attribute_map.items():
        assert attr in ScrollableSearchResultWorkflowSummary.attribute_map
        assert (
            ScrollableSearchResultWorkflowSummary.attribute_map[attr] == json_key
        ), f"JSON mapping for '{attr}' changed from '{json_key}'"


def test_property_getters_backward_compatibility(mock_workflow_summary):
    """Test that property getters work as expected."""
    obj = ScrollableSearchResultWorkflowSummary()

    # Getters should return None initially
    assert obj.results is None
    assert obj.query_id is None

    # Getters should return set values
    test_results = [mock_workflow_summary]
    test_query_id = "test_query"

    obj.results = test_results
    obj.query_id = test_query_id

    assert obj.results == test_results
    assert obj.query_id == test_query_id


def test_property_setters_backward_compatibility(mock_workflow_summary):
    """Test that property setters work as expected."""
    obj = ScrollableSearchResultWorkflowSummary()

    # Test results setter
    test_results = [mock_workflow_summary]
    obj.results = test_results
    assert obj._results == test_results
    assert obj.results == test_results

    # Test query_id setter
    test_query_id = "test_query"
    obj.query_id = test_query_id
    assert obj._query_id == test_query_id
    assert obj.query_id == test_query_id

    # Test setting None values (original behavior)
    obj.results = None
    obj.query_id = None
    assert obj.results is None
    assert obj.query_id is None


def test_to_dict_backward_compatibility(mock_workflow_summary):
    """Test that to_dict method maintains backward compatibility."""
    obj = ScrollableSearchResultWorkflowSummary()

    # Empty object should return dict with None values
    result = obj.to_dict()
    assert isinstance(result, dict)
    assert "results" in result
    assert "query_id" in result

    # With values
    obj.results = [mock_workflow_summary]
    obj.query_id = "test_query"

    result = obj.to_dict()
    assert isinstance(result, dict)
    assert result["query_id"] == "test_query"
    assert isinstance(result["results"], list)


def test_to_str_backward_compatibility():
    """Test that to_str method works as expected."""
    obj = ScrollableSearchResultWorkflowSummary()
    result = obj.to_str()
    assert isinstance(result, str)

    # Should contain the class data representation
    obj.query_id = "test"
    result = obj.to_str()
    assert "test" in result


def test_repr_backward_compatibility():
    """Test that __repr__ method works as expected."""
    obj = ScrollableSearchResultWorkflowSummary()
    result = repr(obj)
    assert isinstance(result, str)


def test_equality_backward_compatibility():
    """Test that equality comparison works as expected."""
    obj1 = ScrollableSearchResultWorkflowSummary()
    obj2 = ScrollableSearchResultWorkflowSummary()

    # Empty objects should be equal
    assert obj1 == obj2

    # Objects with same values should be equal
    obj1.query_id = "test"
    obj2.query_id = "test"
    assert obj1 == obj2

    # Objects with different values should not be equal
    obj2.query_id = "different"
    assert obj1 != obj2

    # Comparison with different type should return False
    assert obj1 != "not_an_object"


def test_initialization_with_values_backward_compatibility(mock_workflow_summary):
    """Test initialization with values maintains backward compatibility."""
    test_results = [mock_workflow_summary]
    test_query_id = "test_query_123"

    obj = ScrollableSearchResultWorkflowSummary(
        results=test_results, query_id=test_query_id
    )

    # Values should be set correctly
    assert obj.results == test_results
    assert obj.query_id == test_query_id
    assert obj._results == test_results
    assert obj._query_id == test_query_id


def test_field_types_not_changed(mock_workflow_summary):
    """Test that field types haven't changed from original specification."""
    obj = ScrollableSearchResultWorkflowSummary()

    # Test with correct types
    obj.results = [mock_workflow_summary]  # Should accept list
    obj.query_id = "string_value"  # Should accept string

    # Values should be set successfully
    assert isinstance(obj.results, list)
    assert isinstance(obj.query_id, str)


def test_original_behavior_preserved(mock_workflow_summary):
    """Test that original behavior is preserved."""
    # Test 1: Default initialization
    obj = ScrollableSearchResultWorkflowSummary()
    assert obj.results is None
    assert obj.query_id is None
    assert obj.discriminator is None

    # Test 2: Partial initialization
    obj = ScrollableSearchResultWorkflowSummary(query_id="test")
    assert obj.results is None
    assert obj.query_id == "test"

    # Test 3: Full initialization
    test_results = [mock_workflow_summary]
    obj = ScrollableSearchResultWorkflowSummary(results=test_results, query_id="test")
    assert obj.results == test_results
    assert obj.query_id == "test"


def test_discriminator_field_preserved():
    """Test that discriminator field is preserved (swagger requirement)."""
    obj = ScrollableSearchResultWorkflowSummary()
    assert hasattr(obj, "discriminator")
    assert obj.discriminator is None


def test_private_attributes_preserved():
    """Test that private attributes are preserved."""
    obj = ScrollableSearchResultWorkflowSummary()

    # Private attributes should exist and be None initially
    assert hasattr(obj, "_results")
    assert hasattr(obj, "_query_id")
    assert obj._results is None
    assert obj._query_id is None
