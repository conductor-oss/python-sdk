import pytest

from conductor.client.adapters.models.start_workflow_request_adapter import StartWorkflowRequestAdapter as StartWorkflowRequest
from conductor.shared.http.enums import IdempotencyStrategy


@pytest.fixture
def valid_name():
    """Set up test fixture with valid name."""
    return "test_workflow"


@pytest.fixture
def valid_version():
    """Set up test fixture with valid version."""
    return 1


@pytest.fixture
def valid_correlation_id():
    """Set up test fixture with valid correlation id."""
    return "test-correlation-id"


@pytest.fixture
def valid_input():
    """Set up test fixture with valid input."""
    return {"key": "value"}


@pytest.fixture
def valid_task_to_domain():
    """Set up test fixture with valid task to domain."""
    return {"task1": "domain1"}


@pytest.fixture
def valid_priority():
    """Set up test fixture with valid priority."""
    return 5


@pytest.fixture
def valid_created_by():
    """Set up test fixture with valid created by."""
    return "test_user"


@pytest.fixture
def valid_idempotency_key():
    """Set up test fixture with valid idempotency key."""
    return "test-key"


@pytest.fixture
def valid_external_path():
    """Set up test fixture with valid external path."""
    return "/path/to/storage"


def test_required_fields_still_exist(valid_name):
    """Test that all existing required fields still exist."""
    # 'name' is the only required field - constructor should work with just name
    request = StartWorkflowRequest(name=valid_name)
    assert request.name == valid_name

    # Verify the field exists and is accessible
    assert hasattr(request, "name")
    assert hasattr(request, "_name")


def test_all_existing_fields_still_exist(valid_name):
    """Test that all existing fields (required and optional) still exist."""
    expected_fields = [
        "name",
        "version",
        "correlation_id",
        "input",
        "task_to_domain",
        "workflow_def",
        "external_input_payload_storage_path",
        "priority",
        "created_by",
        "idempotency_key",
        "idempotency_strategy",
    ]

    request = StartWorkflowRequest(name=valid_name)

    for field in expected_fields:
        # Check property exists
        assert hasattr(request, field), f"Field '{field}' no longer exists"
        # Check private attribute exists
        private_field = f"_{field}"
        assert hasattr(
            request, private_field
        ), f"Private field '{private_field}' no longer exists"


def test_field_types_unchanged(
    valid_name,
    valid_version,
    valid_correlation_id,
    valid_input,
    valid_task_to_domain,
    valid_priority,
    valid_created_by,
    valid_idempotency_key,
    valid_external_path,
):
    """Test that existing field types haven't changed."""
    expected_types = {
        "name": str,
        "version": (int, type(None)),
        "correlation_id": (str, type(None)),
        "input": (dict, type(None)),
        "task_to_domain": (dict, type(None)),
        "priority": (int, type(None)),
        "created_by": (str, type(None)),
        "idempotency_key": (str, type(None)),
        "external_input_payload_storage_path": (str, type(None)),
    }

    request = StartWorkflowRequest(
        name=valid_name,
        version=valid_version,
        correlation_id=valid_correlation_id,
        input=valid_input,
        task_to_domain=valid_task_to_domain,
        priority=valid_priority,
        created_by=valid_created_by,
        idempotency_key=valid_idempotency_key,
        external_input_payload_storage_path=valid_external_path,
    )

    for field, expected_type in expected_types.items():
        value = getattr(request, field)
        if isinstance(expected_type, tuple):
            assert isinstance(value, expected_type), f"Field '{field}' type changed"
        else:
            assert isinstance(value, expected_type), f"Field '{field}' type changed"


def test_constructor_backward_compatibility(
    valid_name,
    valid_version,
    valid_correlation_id,
    valid_input,
    valid_task_to_domain,
    valid_priority,
    valid_created_by,
    valid_idempotency_key,
    valid_external_path,
):
    """Test that constructor signature remains backward compatible."""
    # Test with minimal required parameters (original behavior)
    request1 = StartWorkflowRequest(name=valid_name)
    assert request1.name == valid_name

    # Test with all original parameters
    request2 = StartWorkflowRequest(
        name=valid_name,
        version=valid_version,
        correlation_id=valid_correlation_id,
        input=valid_input,
        task_to_domain=valid_task_to_domain,
        workflow_def=None,  # This would be a WorkflowDef object
        external_input_payload_storage_path=valid_external_path,
        priority=valid_priority,
        created_by=valid_created_by,
        idempotency_key=valid_idempotency_key,
        idempotency_strategy=IdempotencyStrategy.RETURN_EXISTING,
    )

    # Verify all values are set correctly
    assert request2.name == valid_name
    assert request2.version == valid_version
    assert request2.correlation_id == valid_correlation_id
    assert request2.input == valid_input
    assert request2.task_to_domain == valid_task_to_domain
    assert request2.priority == valid_priority
    assert request2.created_by == valid_created_by
    assert request2.idempotency_key == valid_idempotency_key
    assert request2.idempotency_strategy == IdempotencyStrategy.RETURN_EXISTING


def test_property_setters_still_work(
    valid_name,
    valid_version,
    valid_correlation_id,
    valid_input,
    valid_task_to_domain,
    valid_priority,
    valid_created_by,
    valid_idempotency_key,
):
    """Test that all property setters still work as expected."""
    request = StartWorkflowRequest(name=valid_name)

    # Test setting each property
    request.version = valid_version
    assert request.version == valid_version

    request.correlation_id = valid_correlation_id
    assert request.correlation_id == valid_correlation_id

    request.input = valid_input
    assert request.input == valid_input

    request.task_to_domain = valid_task_to_domain
    assert request.task_to_domain == valid_task_to_domain

    request.priority = valid_priority
    assert request.priority == valid_priority

    request.created_by = valid_created_by
    assert request.created_by == valid_created_by

    request.idempotency_key = valid_idempotency_key
    assert request.idempotency_key == valid_idempotency_key

    request.idempotency_strategy = IdempotencyStrategy.RETURN_EXISTING
    assert request.idempotency_strategy == IdempotencyStrategy.RETURN_EXISTING


def test_enum_values_still_exist(valid_name):
    """Test that existing enum values haven't been removed."""
    # Test that existing IdempotencyStrategy values still exist
    assert hasattr(IdempotencyStrategy, "FAIL")
    assert hasattr(IdempotencyStrategy, "RETURN_EXISTING")

    # Test that enum values work as expected
    assert IdempotencyStrategy.FAIL == "FAIL"
    assert IdempotencyStrategy.RETURN_EXISTING == "RETURN_EXISTING"

    # Test that enum values can be used in the model
    request = StartWorkflowRequest(
        name=valid_name, idempotency_strategy=IdempotencyStrategy.FAIL
    )
    assert request.idempotency_strategy == IdempotencyStrategy.FAIL

    request.idempotency_strategy = IdempotencyStrategy.RETURN_EXISTING
    assert request.idempotency_strategy == IdempotencyStrategy.RETURN_EXISTING


def test_idempotency_default_behavior(valid_name, valid_idempotency_key):
    """Test that idempotency default behavior is preserved."""
    # When no idempotency_key is provided, strategy should default to FAIL
    request1 = StartWorkflowRequest(name=valid_name)
    assert request1.idempotency_key is None
    assert request1.idempotency_strategy == IdempotencyStrategy.FAIL

    # When idempotency_key is provided without strategy, should default to FAIL
    request2 = StartWorkflowRequest(
        name=valid_name, idempotency_key=valid_idempotency_key
    )
    assert request2.idempotency_key == valid_idempotency_key
    assert request2.idempotency_strategy == IdempotencyStrategy.FAIL

    # When both are provided, should use provided strategy
    request3 = StartWorkflowRequest(
        name=valid_name,
        idempotency_key=valid_idempotency_key,
        idempotency_strategy=IdempotencyStrategy.RETURN_EXISTING,
    )
    assert request3.idempotency_key == valid_idempotency_key
    assert request3.idempotency_strategy == IdempotencyStrategy.RETURN_EXISTING


def test_swagger_types_dict_exists():
    """Test that swagger_types class attribute still exists with expected mappings."""
    assert hasattr(StartWorkflowRequest, "swagger_types")

    expected_swagger_types = {
        "name": "str",
        "version": "int",
        "correlation_id": "str",
        "input": "dict(str, object)",
        "task_to_domain": "dict(str, str)",
        "workflow_def": "WorkflowDef",
        "external_input_payload_storage_path": "str",
        "priority": "int",
        "created_by": "str",
        "idempotency_key": "str",
        "idempotency_strategy": "str",
    }

    swagger_types = StartWorkflowRequest.swagger_types

    for field, expected_type in expected_swagger_types.items():
        assert field in swagger_types, f"Field '{field}' missing from swagger_types"
        assert (
            swagger_types[field] == expected_type
        ), f"Field '{field}' type changed in swagger_types"


def test_attribute_map_exists():
    """Test that attribute_map class attribute still exists with expected mappings."""
    assert hasattr(StartWorkflowRequest, "attribute_map")

    expected_attribute_map = {
        "name": "name",
        "version": "version",
        "correlation_id": "correlationId",
        "input": "input",
        "task_to_domain": "taskToDomain",
        "workflow_def": "workflowDef",
        "external_input_payload_storage_path": "externalInputPayloadStoragePath",
        "priority": "priority",
        "created_by": "createdBy",
        "idempotency_key": "idempotencyKey",
        "idempotency_strategy": "idempotencyStrategy",
    }

    attribute_map = StartWorkflowRequest.attribute_map

    for field, expected_json_key in expected_attribute_map.items():
        assert field in attribute_map, f"Field '{field}' missing from attribute_map"
        assert (
            attribute_map[field] == expected_json_key
        ), f"Field '{field}' JSON mapping changed in attribute_map"


def test_to_dict_method_exists(valid_name, valid_version, valid_priority):
    """Test that to_dict method still exists and works."""
    request = StartWorkflowRequest(
        name=valid_name, version=valid_version, priority=valid_priority
    )

    assert hasattr(request, "to_dict")
    result = request.to_dict()
    assert isinstance(result, dict)

    # Check that basic fields are present in the dict
    assert "name" in result
    assert result["name"] == valid_name


def test_equality_methods_exist(valid_name):
    """Test that __eq__ and __ne__ methods still exist and work."""
    request1 = StartWorkflowRequest(name=valid_name)
    request2 = StartWorkflowRequest(name=valid_name)
    request3 = StartWorkflowRequest(name="different_name")

    # Test __eq__
    assert hasattr(request1, "__eq__")
    assert request1 == request2
    assert request1 != request3

    # Test __ne__
    assert hasattr(request1, "__ne__")
    assert not (request1 != request2)
    assert request1 != request3


def test_string_methods_exist(valid_name):
    """Test that string representation methods still exist."""
    request = StartWorkflowRequest(name=valid_name)

    # Test to_str method
    assert hasattr(request, "to_str")
    str_result = request.to_str()
    assert isinstance(str_result, str)

    # Test __repr__ method
    assert hasattr(request, "__repr__")
    repr_result = repr(request)
    assert isinstance(repr_result, str)
