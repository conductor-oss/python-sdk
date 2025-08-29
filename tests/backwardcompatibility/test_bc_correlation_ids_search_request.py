import pytest

from conductor.client.http.models.correlation_ids_search_request import (
    CorrelationIdsSearchRequest,
)


@pytest.fixture
def valid_correlation_ids():
    return ["corr-123", "corr-456"]


@pytest.fixture
def valid_workflow_names():
    return ["workflow1", "workflow2"]


def test_constructor_signature_compatibility(
    valid_correlation_ids, valid_workflow_names
):
    """Test that constructor signature hasn't changed."""
    # Test constructor with no arguments (all optional)
    request = CorrelationIdsSearchRequest()
    assert request is not None
    # Test constructor with correlation_ids only
    request = CorrelationIdsSearchRequest(correlation_ids=valid_correlation_ids)
    assert request.correlation_ids == valid_correlation_ids
    # Test constructor with workflow_names only
    request = CorrelationIdsSearchRequest(workflow_names=valid_workflow_names)
    assert request.workflow_names == valid_workflow_names
    # Test constructor with both parameters
    request = CorrelationIdsSearchRequest(
        correlation_ids=valid_correlation_ids, workflow_names=valid_workflow_names
    )
    assert request.correlation_ids == valid_correlation_ids
    assert request.workflow_names == valid_workflow_names


def test_required_fields_exist():
    """Test that all expected fields still exist."""
    request = CorrelationIdsSearchRequest()
    # Test that properties exist and are accessible
    assert hasattr(request, "correlation_ids")
    assert hasattr(request, "workflow_names")
    # Test that private attributes exist
    assert hasattr(request, "_correlation_ids")
    assert hasattr(request, "_workflow_names")


def test_field_types_unchanged():
    """Test that field types haven't changed."""
    # Check swagger_types dictionary exists and contains expected types
    assert hasattr(CorrelationIdsSearchRequest, "swagger_types")
    swagger_types = CorrelationIdsSearchRequest.swagger_types
    assert "correlation_ids" in swagger_types
    assert "workflow_names" in swagger_types
    assert swagger_types["correlation_ids"] == "list[str]"
    assert swagger_types["workflow_names"] == "list[str]"


def test_attribute_mapping_unchanged():
    """Test that attribute mapping hasn't changed."""
    # Check attribute_map dictionary exists and contains expected mappings
    assert hasattr(CorrelationIdsSearchRequest, "attribute_map")
    attribute_map = CorrelationIdsSearchRequest.attribute_map
    assert "correlation_ids" in attribute_map
    assert "workflow_names" in attribute_map
    assert attribute_map["correlation_ids"] == "correlationIds"
    assert attribute_map["workflow_names"] == "workflowNames"


def test_correlation_ids_property_behavior(valid_correlation_ids):
    """Test correlation_ids property getter/setter behavior."""
    request = CorrelationIdsSearchRequest()
    # Test initial value
    assert request.correlation_ids is None
    # Test setter with valid list
    request.correlation_ids = valid_correlation_ids
    assert request.correlation_ids == valid_correlation_ids
    # Test setter with None
    request.correlation_ids = None
    assert request.correlation_ids is None
    # Test setter with empty list
    request.correlation_ids = []
    assert request.correlation_ids == []


def test_workflow_names_property_behavior(valid_workflow_names):
    """Test workflow_names property getter/setter behavior."""
    request = CorrelationIdsSearchRequest()
    # Test initial value
    assert request.workflow_names is None
    # Test setter with valid list
    request.workflow_names = valid_workflow_names
    assert request.workflow_names == valid_workflow_names
    # Test setter with None
    request.workflow_names = None
    assert request.workflow_names is None
    # Test setter with empty list
    request.workflow_names = []
    assert request.workflow_names == []


def test_to_dict_method_compatibility(valid_workflow_names, valid_correlation_ids):
    """Test that to_dict method works as expected."""
    request = CorrelationIdsSearchRequest(
        correlation_ids=valid_correlation_ids, workflow_names=valid_workflow_names
    )
    result_dict = request.to_dict()
    # Test that method exists and returns dict
    assert isinstance(result_dict, dict)
    # Test that expected fields are present in dict
    assert "correlation_ids" in result_dict
    assert "workflow_names" in result_dict
    assert result_dict["correlation_ids"] == valid_correlation_ids
    assert result_dict["workflow_names"] == valid_workflow_names


def test_to_str_method_compatibility(valid_workflow_names, valid_correlation_ids):
    """Test that to_str method works as expected."""
    request = CorrelationIdsSearchRequest(
        correlation_ids=valid_correlation_ids, workflow_names=valid_workflow_names
    )
    result_str = request.to_str()
    # Test that method exists and returns string
    assert isinstance(result_str, str)
    assert len(result_str) > 0


def test_repr_method_compatibility(valid_correlation_ids, valid_workflow_names):
    """Test that __repr__ method works as expected."""
    request = CorrelationIdsSearchRequest(
        correlation_ids=valid_correlation_ids, workflow_names=valid_workflow_names
    )
    repr_str = repr(request)
    # Test that method exists and returns string
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


def test_equality_methods_compatibility(valid_correlation_ids, valid_workflow_names):
    """Test that equality methods work as expected."""
    request1 = CorrelationIdsSearchRequest(
        correlation_ids=valid_correlation_ids, workflow_names=valid_workflow_names
    )
    request2 = CorrelationIdsSearchRequest(
        correlation_ids=valid_correlation_ids, workflow_names=valid_workflow_names
    )
    request3 = CorrelationIdsSearchRequest(
        correlation_ids=["different"], workflow_names=valid_workflow_names
    )
    # Test equality
    assert request1 == request2
    assert request1 != request3
    # Test inequality
    assert not (request1 != request2)
    assert request1 != request3
    # Test inequality with different type
    assert request1 != "not a request object"


def test_discriminator_attribute_exists():
    """Test that discriminator attribute exists and behaves correctly."""
    request = CorrelationIdsSearchRequest()
    assert hasattr(request, "discriminator")
    assert request.discriminator is None


def test_field_assignment_after_construction(
    valid_correlation_ids, valid_workflow_names
):
    """Test that fields can be assigned after construction."""
    request = CorrelationIdsSearchRequest()
    # Test assignment after construction
    request.correlation_ids = valid_correlation_ids
    request.workflow_names = valid_workflow_names
    assert request.correlation_ids == valid_correlation_ids
    assert request.workflow_names == valid_workflow_names


def test_none_values_handling():
    """Test that None values are handled correctly."""
    # Test construction with None values
    request = CorrelationIdsSearchRequest(correlation_ids=None, workflow_names=None)
    assert request.correlation_ids is None
    assert request.workflow_names is None
    # Test to_dict with None values
    result_dict = request.to_dict()
    assert "correlation_ids" in result_dict
    assert "workflow_names" in result_dict
    assert result_dict["correlation_ids"] is None
    assert result_dict["workflow_names"] is None
