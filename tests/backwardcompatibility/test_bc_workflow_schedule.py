import pytest

from conductor.client.http.models import WorkflowSchedule


@pytest.fixture
def mock_start_workflow_request(mocker):
    """Set up test fixture with mock StartWorkflowRequest."""
    mock_request = mocker.Mock()
    mock_request.to_dict.return_value = {"mocked": "data"}
    return mock_request


@pytest.fixture
def valid_data(mock_start_workflow_request):
    """Set up test fixture with valid data for all known fields."""
    return {
        "name": "test_schedule",
        "cron_expression": "0 0 * * *",
        "run_catchup_schedule_instances": True,
        "paused": False,
        "start_workflow_request": mock_start_workflow_request,
        "schedule_start_time": 1640995200,  # Unix timestamp
        "schedule_end_time": 1672531200,
        "create_time": 1640995200,
        "updated_time": 1641081600,
        "created_by": "test_user",
        "updated_by": "test_user_2",
        "description": "Test schedule description",
        "paused_reason": "Test pause reason",
        "tags": [],
        "zone_id": "UTC",
    }


def test_constructor_with_no_parameters():
    """Test that constructor works with no parameters (all defaults to None)."""
    schedule = WorkflowSchedule()

    # All fields should be None initially
    assert schedule.name is None
    assert schedule.cron_expression is None
    assert schedule.run_catchup_schedule_instances is None
    assert schedule.paused is None
    assert schedule.start_workflow_request is None
    assert schedule.schedule_start_time is None
    assert schedule.schedule_end_time is None
    assert schedule.create_time is None
    assert schedule.updated_time is None
    assert schedule.created_by is None
    assert schedule.updated_by is None
    assert schedule.description is None
    assert schedule.paused_reason is None
    assert schedule.tags is None
    assert schedule.zone_id is None


def test_constructor_with_all_parameters(valid_data, mock_start_workflow_request):
    """Test constructor with all existing parameters."""
    schedule = WorkflowSchedule(**valid_data)

    # Verify all fields are set correctly
    assert schedule.name == "test_schedule"
    assert schedule.cron_expression == "0 0 * * *"
    assert schedule.run_catchup_schedule_instances
    assert not schedule.paused
    assert schedule.start_workflow_request == mock_start_workflow_request
    assert schedule.schedule_start_time == 1640995200
    assert schedule.schedule_end_time == 1672531200
    assert schedule.create_time == 1640995200
    assert schedule.updated_time == 1641081600
    assert schedule.created_by == "test_user"
    assert schedule.updated_by == "test_user_2"
    assert schedule.description == "Test schedule description"
    assert schedule.paused_reason == "Test pause reason"
    assert schedule.tags == []
    assert schedule.zone_id == "UTC"


def test_constructor_with_partial_parameters():
    """Test constructor with only some parameters."""
    partial_data = {
        "name": "partial_schedule",
        "cron_expression": "0 12 * * *",
        "paused": True,
    }
    schedule = WorkflowSchedule(**partial_data)

    # Specified fields should be set
    assert schedule.name == "partial_schedule"
    assert schedule.cron_expression == "0 12 * * *"
    assert schedule.paused

    # Unspecified fields should be None
    assert schedule.run_catchup_schedule_instances is None
    assert schedule.start_workflow_request is None
    assert schedule.schedule_start_time is None


def test_all_required_properties_exist():
    """Test that all expected properties exist and are accessible."""
    schedule = WorkflowSchedule()

    # Test that all properties exist (should not raise AttributeError)
    required_properties = [
        "name",
        "cron_expression",
        "run_catchup_schedule_instances",
        "paused",
        "start_workflow_request",
        "schedule_start_time",
        "schedule_end_time",
        "create_time",
        "updated_time",
        "created_by",
        "updated_by",
        "description",
        "paused_reason",
        "tags",
        "zone_id",
    ]

    for prop in required_properties:
        # Test getter exists
        assert hasattr(schedule, prop), f"Property '{prop}' should exist"
        # Test getter works
        getattr(schedule, prop)


def test_property_setters_work(mock_start_workflow_request):
    """Test that all property setters work correctly."""
    schedule = WorkflowSchedule()

    # Test string properties
    schedule.name = "new_name"
    assert schedule.name == "new_name"

    schedule.cron_expression = "0 6 * * *"
    assert schedule.cron_expression == "0 6 * * *"

    schedule.created_by = "setter_user"
    assert schedule.created_by == "setter_user"

    schedule.updated_by = "setter_user_2"
    assert schedule.updated_by == "setter_user_2"

    schedule.description = "New description"
    assert schedule.description == "New description"

    schedule.paused_reason = "New pause reason"
    assert schedule.paused_reason == "New pause reason"

    schedule.zone_id = "EST"
    assert schedule.zone_id == "EST"

    # Test boolean properties
    schedule.run_catchup_schedule_instances = False
    assert not schedule.run_catchup_schedule_instances

    schedule.paused = True
    assert schedule.paused

    # Test integer properties
    schedule.schedule_start_time = 999999999
    assert schedule.schedule_start_time == 999999999

    schedule.schedule_end_time = 888888888
    assert schedule.schedule_end_time == 888888888

    schedule.create_time = 777777777
    assert schedule.create_time == 777777777

    schedule.updated_time = 666666666
    assert schedule.updated_time == 666666666

    # Test object property
    schedule.start_workflow_request = mock_start_workflow_request
    assert schedule.start_workflow_request == mock_start_workflow_request

    # Test list property
    schedule.tags = [{"key": "value"}]
    assert schedule.tags == [{"key": "value"}]


def test_property_types_are_preserved(valid_data, mock_start_workflow_request):
    """Test that property types match expected swagger_types."""
    schedule = WorkflowSchedule(**valid_data)

    # String fields
    assert isinstance(schedule.name, str)
    assert isinstance(schedule.cron_expression, str)
    assert isinstance(schedule.created_by, str)
    assert isinstance(schedule.updated_by, str)
    assert isinstance(schedule.description, str)
    assert isinstance(schedule.paused_reason, str)
    assert isinstance(schedule.zone_id, str)

    # Boolean fields
    assert isinstance(schedule.run_catchup_schedule_instances, bool)
    assert isinstance(schedule.paused, bool)

    # Integer fields
    assert isinstance(schedule.schedule_start_time, int)
    assert isinstance(schedule.schedule_end_time, int)
    assert isinstance(schedule.create_time, int)
    assert isinstance(schedule.updated_time, int)

    # Object field (StartWorkflowRequest)
    assert schedule.start_workflow_request == mock_start_workflow_request

    # List field
    assert isinstance(schedule.tags, list)


def test_swagger_types_attribute_exists():
    """Test that swagger_types class attribute exists and contains expected fields."""
    assert hasattr(WorkflowSchedule, "swagger_types")
    swagger_types = WorkflowSchedule.swagger_types

    expected_types = {
        "name": "str",
        "cron_expression": "str",
        "run_catchup_schedule_instances": "bool",
        "paused": "bool",
        "start_workflow_request": "StartWorkflowRequest",
        "schedule_start_time": "int",
        "schedule_end_time": "int",
        "create_time": "int",
        "updated_time": "int",
        "created_by": "str",
        "updated_by": "str",
        "description": "str",
        "paused_reason": "str",
        "tags": "list[Tag]",
        "zone_id": "str",
    }

    # Check that all expected fields exist with correct types
    for field, expected_type in expected_types.items():
        assert field in swagger_types, f"Field '{field}' should exist in swagger_types"
        assert (
            swagger_types[field] == expected_type
        ), f"Field '{field}' should have type '{expected_type}'"


def test_attribute_map_exists():
    """Test that attribute_map class attribute exists and contains expected mappings."""
    assert hasattr(WorkflowSchedule, "attribute_map")
    attribute_map = WorkflowSchedule.attribute_map

    expected_mappings = {
        "name": "name",
        "cron_expression": "cronExpression",
        "run_catchup_schedule_instances": "runCatchupScheduleInstances",
        "paused": "paused",
        "start_workflow_request": "startWorkflowRequest",
        "schedule_start_time": "scheduleStartTime",
        "schedule_end_time": "scheduleEndTime",
        "create_time": "createTime",
        "updated_time": "updatedTime",
        "created_by": "createdBy",
        "updated_by": "updatedBy",
        "description": "description",
        "paused_reason": "pausedReason",
        "tags": "tags",
        "zone_id": "zoneId",
    }

    # Check that all expected mappings exist
    for field, expected_json_key in expected_mappings.items():
        assert field in attribute_map, f"Field '{field}' should exist in attribute_map"
        assert (
            attribute_map[field] == expected_json_key
        ), f"Field '{field}' should map to '{expected_json_key}'"


def test_to_dict_method_exists_and_works(valid_data):
    """Test that to_dict method exists and produces expected output."""
    schedule = WorkflowSchedule(**valid_data)

    # Method should exist
    assert hasattr(schedule, "to_dict")
    assert callable(getattr(schedule, "to_dict"))

    # Method should return a dictionary
    result = schedule.to_dict()
    assert isinstance(result, dict)

    # Should contain all the fields we set
    assert "name" in result
    assert "cron_expression" in result
    assert "run_catchup_schedule_instances" in result
    assert "paused" in result
    assert "start_workflow_request" in result
    assert "description" in result
    assert "paused_reason" in result
    assert "tags" in result
    assert "zone_id" in result

    # Values should match
    assert result["name"] == "test_schedule"
    assert result["cron_expression"] == "0 0 * * *"
    assert result["run_catchup_schedule_instances"]
    assert not result["paused"]
    assert result["description"] == "Test schedule description"
    assert result["paused_reason"] == "Test pause reason"
    assert result["tags"] == []
    assert result["zone_id"] == "UTC"


def test_to_str_method_exists_and_works():
    """Test that to_str method exists and returns string representation."""
    schedule = WorkflowSchedule(name="test", cron_expression="0 0 * * *")

    # Method should exist
    assert hasattr(schedule, "to_str")
    assert callable(getattr(schedule, "to_str"))

    # Method should return a string
    result = schedule.to_str()
    assert isinstance(result, str)
    assert len(result) > 0


def test_repr_method_works():
    """Test that __repr__ method works."""
    schedule = WorkflowSchedule(name="test")

    # Should return a string representation
    repr_str = repr(schedule)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


def test_equality_methods_exist_and_work():
    """Test that __eq__ and __ne__ methods exist and work correctly."""
    schedule1 = WorkflowSchedule(name="test", paused=True)
    schedule2 = WorkflowSchedule(name="test", paused=True)
    schedule3 = WorkflowSchedule(name="different", paused=True)

    # Test equality
    assert schedule1 == schedule2
    assert schedule1 != schedule3

    # Test inequality
    assert not (schedule1 != schedule2)
    assert schedule1 != schedule3

    # Test with non-WorkflowSchedule object
    assert schedule1 != "not a schedule"
    assert schedule1 != "not a schedule"


def test_discriminator_attribute_exists():
    """Test that discriminator attribute exists and is set to None."""
    schedule = WorkflowSchedule()
    assert hasattr(schedule, "discriminator")
    assert schedule.discriminator is None


def test_private_attributes_exist():
    """Test that all private attributes are properly initialized."""
    schedule = WorkflowSchedule()

    private_attrs = [
        "_name",
        "_cron_expression",
        "_run_catchup_schedule_instances",
        "_paused",
        "_start_workflow_request",
        "_schedule_start_time",
        "_schedule_end_time",
        "_create_time",
        "_updated_time",
        "_created_by",
        "_updated_by",
        "_description",
        "_paused_reason",
        "_tags",
        "_zone_id",
    ]

    for attr in private_attrs:
        assert hasattr(schedule, attr), f"Private attribute '{attr}' should exist"
        assert (
            getattr(schedule, attr) is None
        ), f"Private attribute '{attr}' should be None by default"


def test_none_values_are_handled_correctly(valid_data):
    """Test that None values can be set and retrieved correctly."""
    schedule = WorkflowSchedule(**valid_data)

    # Set all fields to None
    schedule.name = None
    schedule.cron_expression = None
    schedule.run_catchup_schedule_instances = None
    schedule.paused = None
    schedule.start_workflow_request = None
    schedule.schedule_start_time = None
    schedule.schedule_end_time = None
    schedule.create_time = None
    schedule.updated_time = None
    schedule.created_by = None
    schedule.updated_by = None
    schedule.description = None
    schedule.paused_reason = None
    schedule.tags = None
    schedule.zone_id = None

    # Verify all are None
    assert schedule.name is None
    assert schedule.cron_expression is None
    assert schedule.run_catchup_schedule_instances is None
    assert schedule.paused is None
    assert schedule.start_workflow_request is None
    assert schedule.schedule_start_time is None
    assert schedule.schedule_end_time is None
    assert schedule.create_time is None
    assert schedule.updated_time is None
    assert schedule.created_by is None
    assert schedule.updated_by is None
    assert schedule.description is None
    assert schedule.paused_reason is None
    assert schedule.tags is None
    assert schedule.zone_id is None


def test_constructor_signature_compatibility(mock_start_workflow_request):
    """Test that constructor signature remains compatible."""
    # Test positional arguments work (in order based on WorkflowSchedule model)
    schedule = WorkflowSchedule(
        "test_name",  # name
        "0 0 * * *",  # cron_expression
        True,  # run_catchup_schedule_instances
        False,  # paused
        mock_start_workflow_request,  # start_workflow_request
        1640995200,  # schedule_start_time
        1672531200,  # schedule_end_time
        1640995200,  # create_time
        1641081600,  # updated_time
        "creator",  # created_by
        "updater",  # updated_by
    )

    assert schedule.name == "test_name"
    assert schedule.cron_expression == "0 0 * * *"
    assert schedule.run_catchup_schedule_instances
    assert not schedule.paused
    assert schedule.created_by == "creator"
    assert schedule.updated_by == "updater"
