import pytest

from conductor.client.adapters.models.search_result_workflow_schedule_execution_model_adapter import SearchResultWorkflowScheduleExecutionModelAdapter


@pytest.fixture
def mock_workflow_execution(mocker):
    """Set up test fixture with mock workflow execution."""
    mock_execution = mocker.Mock()
    mock_execution.to_dict.return_value = {"id": "test_execution_1"}
    return mock_execution


@pytest.fixture
def valid_total_hits():
    """Set up test fixture with valid total hits."""
    return 42


@pytest.fixture
def valid_results(mock_workflow_execution):
    """Set up test fixture with valid results."""
    return [mock_workflow_execution]


def test_constructor_with_no_parameters():
    """Test that model can be constructed with no parameters (backward compatibility)."""
    model = SearchResultWorkflowScheduleExecutionModelAdapter()

    # Verify model is created successfully
    assert model is not None
    assert model.total_hits is None
    assert model.results is None


def test_constructor_with_all_parameters(valid_total_hits, valid_results):
    """Test that model can be constructed with all existing parameters."""
    model = SearchResultWorkflowScheduleExecutionModelAdapter(
        total_hits=valid_total_hits, results=valid_results
    )

    # Verify all fields are set correctly
    assert model.total_hits == valid_total_hits
    assert model.results == valid_results


def test_constructor_with_partial_parameters(valid_total_hits, valid_results):
    """Test constructor with only some parameters (backward compatibility)."""
    # Test with only total_hits
    model1 = SearchResultWorkflowScheduleExecutionModelAdapter(total_hits=valid_total_hits)
    assert model1.total_hits == valid_total_hits
    assert model1.results is None

    # Test with only results
    model2 = SearchResultWorkflowScheduleExecutionModelAdapter(results=valid_results)
    assert model2.total_hits is None
    assert model2.results == valid_results


def test_required_fields_exist():
    """Test that all existing required fields still exist."""
    model = SearchResultWorkflowScheduleExecutionModelAdapter()

    # Verify all expected attributes exist
    required_attributes = ["total_hits", "results"]
    for attr in required_attributes:
        assert hasattr(
            model, attr
        ), f"Required attribute '{attr}' is missing from model"


def test_private_attributes_exist():
    """Test that internal private attributes still exist."""
    model = SearchResultWorkflowScheduleExecutionModelAdapter()

    # Verify private attributes exist (used internally by the model)
    private_attributes = ["_total_hits", "_results", "discriminator"]
    for attr in private_attributes:
        assert hasattr(model, attr), f"Private attribute '{attr}' is missing from model"


def test_swagger_metadata_unchanged():
    """Test that swagger metadata hasn't changed (backward compatibility)."""
    expected_swagger_types = {
        "total_hits": "int",
        "results": "list[WorkflowScheduleExecutionModel]",
    }

    expected_attribute_map = {"total_hits": "totalHits", "results": "results"}

    # Verify swagger_types contains all expected mappings
    for key, expected_type in expected_swagger_types.items():
        assert (
            key in SearchResultWorkflowScheduleExecutionModelAdapter.swagger_types
        ), f"swagger_types missing key '{key}'"
        assert (
            SearchResultWorkflowScheduleExecutionModelAdapter.swagger_types[key]
            == expected_type
        ), f"swagger_types['{key}'] type changed from '{expected_type}'"

    # Verify attribute_map contains all expected mappings
    for key, expected_json_key in expected_attribute_map.items():
        assert (
            key in SearchResultWorkflowScheduleExecutionModelAdapter.attribute_map
        ), f"attribute_map missing key '{key}'"
        assert (
            SearchResultWorkflowScheduleExecutionModelAdapter.attribute_map[key]
            == expected_json_key
        ), f"attribute_map['{key}'] changed from '{expected_json_key}'"


def test_total_hits_property_getter(valid_total_hits):
    """Test that total_hits property getter works correctly."""
    model = SearchResultWorkflowScheduleExecutionModelAdapter()
    model._total_hits = valid_total_hits

    assert model.total_hits == valid_total_hits


def test_total_hits_property_setter(valid_total_hits):
    """Test that total_hits property setter works correctly."""
    model = SearchResultWorkflowScheduleExecutionModelAdapter()

    # Test setting valid value
    model.total_hits = valid_total_hits
    assert model._total_hits == valid_total_hits
    assert model.total_hits == valid_total_hits

    # Test setting None (should be allowed based on current implementation)
    model.total_hits = None
    assert model._total_hits is None
    assert model.total_hits is None


def test_results_property_getter(valid_results):
    """Test that results property getter works correctly."""
    model = SearchResultWorkflowScheduleExecutionModelAdapter()
    model._results = valid_results

    assert model.results == valid_results


def test_results_property_setter(valid_results):
    """Test that results property setter works correctly."""
    model = SearchResultWorkflowScheduleExecutionModelAdapter()

    # Test setting valid value
    model.results = valid_results
    assert model._results == valid_results
    assert model.results == valid_results

    # Test setting None (should be allowed based on current implementation)
    model.results = None
    assert model._results is None
    assert model.results is None

    # Test setting empty list
    empty_results = []
    model.results = empty_results
    assert model._results == empty_results
    assert model.results == empty_results


def test_to_dict_method_exists_and_works(valid_total_hits, valid_results):
    """Test that to_dict method exists and produces expected output."""
    model = SearchResultWorkflowScheduleExecutionModelAdapter(
        total_hits=valid_total_hits, results=valid_results
    )

    # Verify method exists
    assert hasattr(model, "to_dict"), "to_dict method is missing"
    assert callable(getattr(model, "to_dict")), "to_dict is not callable"

    # Test method execution
    result_dict = model.to_dict()
    assert isinstance(result_dict, dict), "to_dict should return a dictionary"

    # Verify expected keys exist in output
    assert "total_hits" in result_dict
    assert "results" in result_dict


def test_to_str_method_exists_and_works():
    """Test that to_str method exists and works."""
    model = SearchResultWorkflowScheduleExecutionModelAdapter()

    # Verify method exists
    assert hasattr(model, "to_str"), "to_str method is missing"
    assert callable(getattr(model, "to_str")), "to_str is not callable"

    # Test method execution
    result_str = model.to_str()
    assert isinstance(result_str, str), "to_str should return a string"


def test_repr_method_exists_and_works():
    """Test that __repr__ method exists and works."""
    model = SearchResultWorkflowScheduleExecutionModelAdapter()

    # Test method execution
    repr_result = repr(model)
    assert isinstance(repr_result, str), "__repr__ should return a string"


def test_equality_methods_exist_and_work(valid_total_hits, valid_results):
    """Test that equality methods (__eq__, __ne__) exist and work correctly."""
    model1 = SearchResultWorkflowScheduleExecutionModelAdapter(
        total_hits=valid_total_hits, results=valid_results
    )
    model2 = SearchResultWorkflowScheduleExecutionModelAdapter(
        total_hits=valid_total_hits, results=valid_results
    )
    model3 = SearchResultWorkflowScheduleExecutionModelAdapter(total_hits=99)

    # Test equality
    assert model1 == model2, "Equal models should be equal"
    assert model1 != model3, "Different models should not be equal"

    # Test inequality with different types
    assert model1 != "not_a_model", "Model should not equal non-model object"

    # Test __ne__ method
    assert not (model1 != model2), "__ne__ should return False for equal models"
    assert model1 != model3, "__ne__ should return True for different models"


def test_field_types_unchanged(valid_results):
    """Test that field types haven't changed from their expected types."""
    model = SearchResultWorkflowScheduleExecutionModelAdapter()

    # Set fields to valid values and verify they accept expected types
    model.total_hits = 42
    assert isinstance(model.total_hits, int), "total_hits should accept int values"

    model.results = valid_results
    assert isinstance(model.results, list), "results should accept list values"


def test_discriminator_attribute_exists():
    """Test that discriminator attribute exists and is properly initialized."""
    model = SearchResultWorkflowScheduleExecutionModelAdapter()

    assert hasattr(model, "discriminator"), "discriminator attribute is missing"
    assert model.discriminator is None, "discriminator should be initialized to None"


def test_class_level_attributes_exist():
    """Test that class-level attributes still exist."""
    cls = SearchResultWorkflowScheduleExecutionModelAdapter

    # Verify class attributes exist
    assert hasattr(cls, "swagger_types"), "swagger_types class attribute is missing"
    assert hasattr(cls, "attribute_map"), "attribute_map class attribute is missing"

    # Verify they are dictionaries
    assert isinstance(cls.swagger_types, dict), "swagger_types should be a dictionary"
    assert isinstance(cls.attribute_map, dict), "attribute_map should be a dictionary"


def test_no_new_required_validations_added():
    """Test that no new required field validations were added that break backward compatibility."""
    # This test ensures that previously optional parameters haven't become required

    # Should be able to create model with no parameters
    try:
        model = SearchResultWorkflowScheduleExecutionModelAdapter()
        assert model is not None
    except Exception as e:
        pytest.fail(
            f"Model creation with no parameters failed: {e}. This breaks backward compatibility."
        )

    # Should be able to set fields to None
    try:
        model = SearchResultWorkflowScheduleExecutionModelAdapter()
        model.total_hits = None
        model.results = None
        assert model.total_hits is None
        assert model.results is None
    except Exception as e:
        pytest.fail(
            f"Setting fields to None failed: {e}. This breaks backward compatibility."
        )
