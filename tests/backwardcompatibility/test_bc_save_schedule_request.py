import pytest

from conductor.client.http.models import SaveScheduleRequest, StartWorkflowRequest


@pytest.fixture
def start_workflow_request():
    """Set up test fixture with StartWorkflowRequest instance."""
    return StartWorkflowRequest() if StartWorkflowRequest else None


@pytest.fixture
def valid_data(start_workflow_request):
    """Set up test fixture with valid data for all existing fields."""
    return {
        "name": "test_schedule",
        "cron_expression": "0 0 * * *",
        "run_catchup_schedule_instances": True,
        "paused": False,
        "start_workflow_request": start_workflow_request,
        "created_by": "test_user",
        "updated_by": "test_user",
        "schedule_start_time": 1640995200,  # Unix timestamp
        "schedule_end_time": 1672531200,  # Unix timestamp
    }


def test_constructor_with_all_existing_fields(valid_data, start_workflow_request):
    """Test that constructor accepts all existing fields without errors."""
    # Test constructor with all fields
    request = SaveScheduleRequest(**valid_data)

    # Verify all fields are set correctly
    assert request.name == "test_schedule"
    assert request.cron_expression == "0 0 * * *"
    assert request.run_catchup_schedule_instances is True
    assert request.paused is False
    assert request.start_workflow_request == start_workflow_request
    assert request.created_by == "test_user"
    assert request.updated_by == "test_user"
    assert request.schedule_start_time == 1640995200
    assert request.schedule_end_time == 1672531200


def test_constructor_with_minimal_required_fields():
    """Test constructor with only required fields (name and cron_expression)."""
    request = SaveScheduleRequest(name="test_schedule", cron_expression="0 0 * * *")

    # Required fields should be set
    assert request.name == "test_schedule"
    assert request.cron_expression == "0 0 * * *"

    # Optional fields should be None or default values
    assert request.run_catchup_schedule_instances is None
    assert request.paused is None
    assert request.start_workflow_request is None
    assert request.created_by is None
    assert request.updated_by is None
    assert request.schedule_start_time is None
    assert request.schedule_end_time is None


def test_all_expected_attributes_exist():
    """Verify all expected attributes exist on the class."""
    expected_attributes = [
        "name",
        "cron_expression",
        "run_catchup_schedule_instances",
        "paused",
        "start_workflow_request",
        "created_by",
        "updated_by",
        "schedule_start_time",
        "schedule_end_time",
    ]

    request = SaveScheduleRequest(name="test", cron_expression="0 0 * * *")

    for attr in expected_attributes:
        assert hasattr(request, attr), f"Missing expected attribute: {attr}"


def test_swagger_types_mapping_exists():
    """Verify swagger_types mapping contains all expected field types."""
    expected_swagger_types = {
        "name": "str",
        "cron_expression": "str",
        "run_catchup_schedule_instances": "bool",
        "paused": "bool",
        "start_workflow_request": "StartWorkflowRequest",
        "created_by": "str",
        "updated_by": "str",
        "schedule_start_time": "int",
        "schedule_end_time": "int",
        'zone_id': 'str',
        'description': 'str',
    }

    for field, expected_type in expected_swagger_types.items():
        assert (
            field in SaveScheduleRequest.swagger_types
        ), f"Missing field in swagger_types: {field}"
        assert (
            SaveScheduleRequest.swagger_types[field] == expected_type
        ), f"Type mismatch for field {field}"


def test_attribute_map_exists():
    """Verify attribute_map contains all expected JSON mappings."""
    expected_attribute_map = {
        "name": "name",
        "cron_expression": "cronExpression",
        "run_catchup_schedule_instances": "runCatchupScheduleInstances",
        "paused": "paused",
        "start_workflow_request": "startWorkflowRequest",
        "created_by": "createdBy",
        "updated_by": "updatedBy",
        "schedule_start_time": "scheduleStartTime",
        "schedule_end_time": "scheduleEndTime",
    }

    for field, expected_json_key in expected_attribute_map.items():
        assert (
            field in SaveScheduleRequest.attribute_map
        ), f"Missing field in attribute_map: {field}"
        assert (
            SaveScheduleRequest.attribute_map[field] == expected_json_key
        ), f"JSON key mismatch for field {field}"


def test_property_getters_exist(valid_data, start_workflow_request):
    """Verify all property getters exist and work correctly."""
    request = SaveScheduleRequest(**valid_data)

    # Test all getters
    assert request.name == "test_schedule"
    assert request.cron_expression == "0 0 * * *"
    assert request.run_catchup_schedule_instances is True
    assert request.paused is False
    assert request.start_workflow_request == start_workflow_request
    assert request.created_by == "test_user"
    assert request.updated_by == "test_user"
    assert request.schedule_start_time == 1640995200
    assert request.schedule_end_time == 1672531200


def test_property_setters_exist(start_workflow_request):
    """Verify all property setters exist and work correctly."""
    request = SaveScheduleRequest(name="test", cron_expression="0 0 * * *")

    # Test all setters
    request.name = "updated_schedule"
    assert request.name == "updated_schedule"

    request.cron_expression = "0 12 * * *"
    assert request.cron_expression == "0 12 * * *"

    request.run_catchup_schedule_instances = False
    assert request.run_catchup_schedule_instances is False

    request.paused = True
    assert request.paused is True

    request.start_workflow_request = start_workflow_request
    assert request.start_workflow_request == start_workflow_request

    request.created_by = "new_user"
    assert request.created_by == "new_user"

    request.updated_by = "another_user"
    assert request.updated_by == "another_user"

    request.schedule_start_time = 1672531200
    assert request.schedule_start_time == 1672531200

    request.schedule_end_time = 1704067200
    assert request.schedule_end_time == 1704067200


def test_field_type_validation_string_fields():
    """Test that string fields accept string values."""
    request = SaveScheduleRequest(name="test", cron_expression="0 0 * * *")

    # String fields should accept string values
    string_fields = ["name", "cron_expression", "created_by", "updated_by"]
    for field in string_fields:
        setattr(request, field, "test_string")
        assert getattr(request, field) == "test_string"


def test_field_type_validation_boolean_fields():
    """Test that boolean fields accept boolean values."""
    request = SaveScheduleRequest(name="test", cron_expression="0 0 * * *")

    # Boolean fields should accept boolean values
    boolean_fields = ["run_catchup_schedule_instances", "paused"]
    for field in boolean_fields:
        setattr(request, field, True)
        assert getattr(request, field) is True
        setattr(request, field, False)
        assert getattr(request, field) is False


def test_field_type_validation_integer_fields():
    """Test that integer fields accept integer values."""
    request = SaveScheduleRequest(name="test", cron_expression="0 0 * * *")

    # Integer fields should accept integer values
    integer_fields = ["schedule_start_time", "schedule_end_time"]
    for field in integer_fields:
        setattr(request, field, 1234567890)
        assert getattr(request, field) == 1234567890


def test_to_dict_method_exists(valid_data):
    """Verify to_dict method exists and includes all expected fields."""
    request = SaveScheduleRequest(**valid_data)
    result_dict = request.to_dict()

    assert isinstance(result_dict, dict)

    # Check that all fields are present in the dictionary
    expected_fields = [
        "name",
        "cron_expression",
        "run_catchup_schedule_instances",
        "paused",
        "start_workflow_request",
        "created_by",
        "updated_by",
        "schedule_start_time",
        "schedule_end_time",
    ]

    for field in expected_fields:
        assert field in result_dict


def test_to_str_method_exists():
    """Verify to_str method exists and returns a string."""
    request = SaveScheduleRequest(name="test", cron_expression="0 0 * * *")
    result = request.to_str()

    assert isinstance(result, str)


def test_repr_method_exists():
    """Verify __repr__ method exists and returns a string."""
    request = SaveScheduleRequest(name="test", cron_expression="0 0 * * *")
    result = repr(request)

    assert isinstance(result, str)


def test_equality_methods_exist():
    """Verify __eq__ and __ne__ methods exist and work correctly."""
    request1 = SaveScheduleRequest(name="test", cron_expression="0 0 * * *")
    request2 = SaveScheduleRequest(name="test", cron_expression="0 0 * * *")
    request3 = SaveScheduleRequest(name="different", cron_expression="0 0 * * *")

    # Test equality
    assert request1 == request2
    assert request1 != request3

    # Test inequality with non-SaveScheduleRequest object
    assert request1 != "not a SaveScheduleRequest"


def test_discriminator_attribute_exists():
    """Verify discriminator attribute exists and is None by default."""
    request = SaveScheduleRequest(name="test", cron_expression="0 0 * * *")
    assert hasattr(request, "discriminator")
    assert request.discriminator is None


def test_private_attributes_exist():
    """Verify all private attributes exist."""
    request = SaveScheduleRequest(name="test", cron_expression="0 0 * * *")

    expected_private_attrs = [
        "_name",
        "_cron_expression",
        "_run_catchup_schedule_instances",
        "_paused",
        "_start_workflow_request",
        "_created_by",
        "_updated_by",
        "_schedule_start_time",
        "_schedule_end_time",
    ]

    for attr in expected_private_attrs:
        assert hasattr(request, attr), f"Missing expected private attribute: {attr}"


def test_none_values_handling():
    """Test that None values are handled correctly for optional fields."""
    request = SaveScheduleRequest(name="test", cron_expression="0 0 * * *")

    # Optional fields should accept None
    optional_fields = [
        "run_catchup_schedule_instances",
        "paused",
        "start_workflow_request",
        "created_by",
        "updated_by",
        "schedule_start_time",
        "schedule_end_time",
    ]

    for field in optional_fields:
        setattr(request, field, None)
        assert getattr(request, field) is None
