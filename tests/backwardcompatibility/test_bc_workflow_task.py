import pytest

from conductor.client.http.models.state_change_event import (
    StateChangeConfig,
    StateChangeEvent,
    StateChangeEventType,
)
from conductor.client.http.models.workflow_task import CacheConfig, WorkflowTask


@pytest.fixture
def valid_cache_config():
    """Set up test fixture with valid cache config."""
    return CacheConfig(key="test_key", ttl_in_second=300)


@pytest.fixture
def valid_state_change_event():
    """Set up test fixture with valid state change event."""
    return StateChangeEvent(
        type="task_status_changed",
        payload={"task": "${task}", "workflow": "${workflow}"},
    )


@pytest.fixture
def valid_state_change_config(valid_state_change_event):
    """Set up test fixture with valid state change config."""
    return StateChangeConfig(
        event_type=StateChangeEventType.onStart, events=[valid_state_change_event]
    )


def test_required_fields_in_constructor():
    """Test that required fields (name, task_reference_name) work in constructor."""
    # Test with only required fields
    task = WorkflowTask(name="test_task", task_reference_name="test_ref")
    assert task.name == "test_task"
    assert task.task_reference_name == "test_ref"


def test_all_existing_fields_accessible(valid_cache_config, valid_state_change_config):
    """Test that all existing fields can be set and retrieved."""
    task = WorkflowTask(
        name="test_task",
        task_reference_name="test_ref",
        description="test description",
        input_parameters={"key": "value"},
        type="SIMPLE",
        dynamic_task_name_param="dynamic_param",
        case_value_param="case_param",
        case_expression="case_expr",
        script_expression="script_expr",
        decision_cases={"case1": []},
        dynamic_fork_join_tasks_param="fork_join_param",
        dynamic_fork_tasks_param="fork_param",
        dynamic_fork_tasks_input_param_name="fork_input_param",
        default_case=[],
        fork_tasks=[[]],
        start_delay=1000,
        sub_workflow_param=None,
        join_on=["task1", "task2"],
        sink="test_sink",
        optional=True,
        task_definition=None,
        rate_limited=False,
        default_exclusive_join_task=["join_task"],
        async_complete=True,
        loop_condition="condition",
        loop_over=[],
        retry_count=3,
        evaluator_type="javascript",
        expression="test_expression",
        workflow_task_type="SIMPLE",
        on_state_change={"onStart": valid_state_change_config.events},
        cache_config=valid_cache_config,
    )

    # Verify all fields are accessible and have correct values
    assert task.name == "test_task"
    assert task.task_reference_name == "test_ref"
    assert task.description == "test description"
    assert task.input_parameters == {"key": "value"}
    assert task.type == "SIMPLE"
    assert task.dynamic_task_name_param == "dynamic_param"
    assert task.case_value_param == "case_param"
    assert task.case_expression == "case_expr"
    assert task.script_expression == "script_expr"
    assert task.decision_cases == {"case1": []}
    assert task.dynamic_fork_join_tasks_param == "fork_join_param"
    assert task.dynamic_fork_tasks_param == "fork_param"
    assert task.dynamic_fork_tasks_input_param_name == "fork_input_param"
    assert task.default_case == []
    assert task.fork_tasks == [[]]
    assert task.start_delay == 1000
    assert task.sub_workflow_param is None
    assert task.join_on == ["task1", "task2"]
    assert task.sink == "test_sink"
    assert task.optional is True
    assert task.task_definition is None
    assert task.rate_limited is False
    assert task.default_exclusive_join_task == ["join_task"]
    assert task.async_complete is True
    assert task.loop_condition == "condition"
    assert task.loop_over == []
    assert task.retry_count == 3
    assert task.evaluator_type == "javascript"
    assert task.expression == "test_expression"
    assert task.workflow_task_type == "SIMPLE"
    assert task.on_state_change == {"onStart": valid_state_change_config.events}
    assert task.cache_config == valid_cache_config


def test_field_types_unchanged(valid_cache_config):
    """Test that existing field types haven't changed."""
    task = WorkflowTask(name="test", task_reference_name="ref")

    # String fields
    task.name = "string_value"
    task.task_reference_name = "string_value"
    task.description = "string_value"
    task.type = "string_value"
    task.dynamic_task_name_param = "string_value"
    task.case_value_param = "string_value"
    task.case_expression = "string_value"
    task.script_expression = "string_value"
    task.dynamic_fork_join_tasks_param = "string_value"
    task.dynamic_fork_tasks_param = "string_value"
    task.dynamic_fork_tasks_input_param_name = "string_value"
    task.sink = "string_value"
    task.loop_condition = "string_value"
    task.evaluator_type = "string_value"
    task.expression = "string_value"
    task.workflow_task_type = "string_value"

    # Dictionary fields
    task.input_parameters = {"key": "value"}
    task.decision_cases = {"case": []}

    # List fields
    task.default_case = []
    task.fork_tasks = [[]]
    task.join_on = ["task1"]
    task.default_exclusive_join_task = ["task1"]
    task.loop_over = []

    # Integer fields
    task.start_delay = 100
    task.retry_count = 5

    # Boolean fields
    task.optional = True
    task.rate_limited = False
    task.async_complete = True

    # Complex object fields
    task.cache_config = valid_cache_config

    # All assignments should succeed without type errors
    assert isinstance(task.name, str)
    assert isinstance(task.input_parameters, dict)
    assert isinstance(task.default_case, list)
    assert isinstance(task.start_delay, int)
    assert isinstance(task.optional, bool)
    assert isinstance(task.cache_config, CacheConfig)


def test_property_setters_work():
    """Test that all property setters continue to work."""
    task = WorkflowTask(name="test", task_reference_name="ref")

    # Test setter functionality
    task.name = "new_name"
    assert task.name == "new_name"

    task.description = "new_description"
    assert task.description == "new_description"

    task.input_parameters = {"new_key": "new_value"}
    assert task.input_parameters == {"new_key": "new_value"}

    task.optional = False
    assert task.optional is False

    task.retry_count = 10
    assert task.retry_count == 10


def test_none_values_accepted():
    """Test that None values are properly handled for optional fields."""
    task = WorkflowTask(name="test", task_reference_name="ref")

    # These fields should accept None
    optional_fields = [
        "description",
        "input_parameters",
        "type",
        "dynamic_task_name_param",
        "case_value_param",
        "case_expression",
        "script_expression",
        "decision_cases",
        "dynamic_fork_join_tasks_param",
        "dynamic_fork_tasks_param",
        "dynamic_fork_tasks_input_param_name",
        "default_case",
        "fork_tasks",
        "start_delay",
        "sub_workflow_param",
        "join_on",
        "sink",
        "optional",
        "task_definition",
        "rate_limited",
        "default_exclusive_join_task",
        "async_complete",
        "loop_condition",
        "loop_over",
        "retry_count",
        "evaluator_type",
        "expression",
        "workflow_task_type",
    ]

    for field in optional_fields:
        setattr(task, field, None)
        assert getattr(task, field) is None


def test_special_properties_behavior():
    """Test special properties like on_state_change that have custom setters."""
    task = WorkflowTask(name="test", task_reference_name="ref")

    # Test on_state_change setter behavior
    state_change_event = StateChangeEvent(
        type="task_status_changed",
        payload={"task": "${task}", "workflow": "${workflow}"},
    )
    state_change_config = StateChangeConfig(
        event_type=StateChangeEventType.onSuccess, events=[state_change_event]
    )
    task.on_state_change = state_change_config

    # The setter should create a dictionary with state_change.type (string) as key
    # and state_change.events as value
    expected_dict = {"onSuccess": state_change_config.events}
    assert task.on_state_change == expected_dict


def test_cache_config_integration():
    """Test CacheConfig integration works as expected."""
    cache_config = CacheConfig(key="test_cache", ttl_in_second=600)
    task = WorkflowTask(
        name="test", task_reference_name="ref", cache_config=cache_config
    )

    assert task.cache_config == cache_config
    assert task.cache_config.key == "test_cache"
    assert task.cache_config.ttl_in_second == 600


def test_to_dict_method_exists():
    """Test that to_dict method exists and works."""
    task = WorkflowTask(name="test", task_reference_name="ref", description="test desc")

    result = task.to_dict()
    assert isinstance(result, dict)
    assert "name" in result
    assert "task_reference_name" in result
    assert "description" in result


def test_str_representation_methods():
    """Test string representation methods exist."""
    task = WorkflowTask(name="test", task_reference_name="ref")

    # Test to_str method
    str_result = task.to_str()
    assert isinstance(str_result, str)

    # Test __repr__ method
    repr_result = repr(task)
    assert isinstance(repr_result, str)


def test_equality_methods():
    """Test equality comparison methods work."""
    task1 = WorkflowTask(name="test", task_reference_name="ref")
    task2 = WorkflowTask(name="test", task_reference_name="ref")
    task3 = WorkflowTask(name="different", task_reference_name="ref")

    # Test __eq__
    assert task1 == task2
    assert task1 != task3

    # Test __ne__
    assert not (task1 != task2)
    assert task1 != task3


def test_swagger_types_attribute_map_exist():
    """Test that swagger_types and attribute_map class attributes exist."""
    assert hasattr(WorkflowTask, "swagger_types")
    assert hasattr(WorkflowTask, "attribute_map")
    assert isinstance(WorkflowTask.swagger_types, dict)
    assert isinstance(WorkflowTask.attribute_map, dict)

    # Test that all expected fields are in swagger_types
    expected_fields = [
        "name",
        "task_reference_name",
        "description",
        "input_parameters",
        "type",
        "dynamic_task_name_param",
        "case_value_param",
        "case_expression",
        "script_expression",
        "decision_cases",
        "dynamic_fork_join_tasks_param",
        "dynamic_fork_tasks_param",
        "dynamic_fork_tasks_input_param_name",
        "default_case",
        "fork_tasks",
        "start_delay",
        "sub_workflow_param",
        "join_on",
        "sink",
        "optional",
        "task_definition",
        "rate_limited",
        "default_exclusive_join_task",
        "async_complete",
        "loop_condition",
        "loop_over",
        "retry_count",
        "evaluator_type",
        "expression",
        "workflow_task_type",
        "on_state_change",
        "cache_config",
    ]

    for field in expected_fields:
        assert field in WorkflowTask.swagger_types
        assert field in WorkflowTask.attribute_map


def test_discriminator_attribute_exists():
    """Test that discriminator attribute exists and is properly set."""
    task = WorkflowTask(name="test", task_reference_name="ref")
    assert hasattr(task, "discriminator")
    assert task.discriminator is None


def test_complex_nested_structures():
    """Test handling of complex nested structures."""
    # Test with nested WorkflowTask structures
    nested_task = WorkflowTask(name="nested", task_reference_name="nested_ref")

    task = WorkflowTask(
        name="parent",
        task_reference_name="parent_ref",
        decision_cases={"case1": [nested_task]},
        default_case=[nested_task],
        fork_tasks=[[nested_task]],
        loop_over=[nested_task],
    )

    assert len(task.decision_cases["case1"]) == 1
    assert task.decision_cases["case1"][0].name == "nested"
    assert len(task.default_case) == 1
    assert task.default_case[0].name == "nested"


def test_cache_config_required_fields():
    """Test CacheConfig constructor with required fields."""
    cache_config = CacheConfig(key="test_key", ttl_in_second=300)
    assert cache_config.key == "test_key"
    assert cache_config.ttl_in_second == 300


def test_cache_config_property_setters():
    """Test CacheConfig property setters work."""
    cache_config = CacheConfig(key="initial", ttl_in_second=100)

    cache_config.key = "updated_key"
    cache_config.ttl_in_second = 500

    assert cache_config.key == "updated_key"
    assert cache_config.ttl_in_second == 500


def test_cache_config_attributes_exist():
    """Test that CacheConfig has required class attributes."""
    assert hasattr(CacheConfig, "swagger_types")
    assert hasattr(CacheConfig, "attribute_map")

    expected_swagger_types = {"key": "str", "ttl_in_second": "int"}
    expected_attribute_map = {"key": "key", "ttl_in_second": "ttlInSecond"}

    assert CacheConfig.swagger_types == expected_swagger_types
    assert CacheConfig.attribute_map == expected_attribute_map
