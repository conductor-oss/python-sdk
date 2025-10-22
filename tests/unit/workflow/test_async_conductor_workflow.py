import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import StartWorkflowRequestAdapter
from conductor.asyncio_client.adapters.models.workflow_def_adapter import WorkflowDefAdapter
from conductor.asyncio_client.adapters.models.workflow_run_adapter import WorkflowRunAdapter
from conductor.asyncio_client.adapters.models.workflow_task_adapter import WorkflowTaskAdapter
from conductor.asyncio_client.workflow.conductor_workflow import AsyncConductorWorkflow, InlineSubWorkflowTask
from conductor.asyncio_client.workflow.executor.workflow_executor import AsyncWorkflowExecutor
from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.http.enums import IdempotencyStrategy
from conductor.shared.workflow.enums import TaskType, TimeoutPolicy


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def mock_executor():
    return AsyncMock(spec=AsyncWorkflowExecutor)


@pytest.fixture
def conductor_workflow(mock_executor):
    return AsyncConductorWorkflow(mock_executor, "test_workflow", 1, "Test workflow")


@pytest.fixture
def mock_task():
    class MockTask(TaskInterface):
        def __init__(self):
            super().__init__("test_task", TaskType.SIMPLE)
            self._mock_workflow_task = MagicMock(spec=WorkflowTaskAdapter)
            self._mock_workflow_task.type = "SIMPLE"

        def to_workflow_task(self):
            return self._mock_workflow_task

    return MockTask()


@pytest.fixture
def mock_workflow_def():
    return MagicMock(spec=WorkflowDefAdapter)


@pytest.fixture
def mock_workflow_run():
    return MagicMock(spec=WorkflowRunAdapter)


def test_init(conductor_workflow, mock_executor):
    assert conductor_workflow._executor == mock_executor
    assert conductor_workflow.name == "test_workflow"
    assert conductor_workflow.version == 1
    assert conductor_workflow.description == "Test workflow"
    assert conductor_workflow._tasks == []
    assert conductor_workflow._owner_email is None
    assert conductor_workflow._timeout_policy is None
    assert conductor_workflow._timeout_seconds == 60
    assert conductor_workflow._failure_workflow == ""
    assert conductor_workflow._input_parameters == []
    assert conductor_workflow._output_parameters == {}
    assert conductor_workflow._input_template == {}
    assert conductor_workflow._variables == {}
    assert conductor_workflow._restartable is True
    assert conductor_workflow._workflow_status_listener_enabled is False
    assert conductor_workflow._workflow_status_listener_sink is None


def test_name_property(conductor_workflow):
    conductor_workflow.name = "new_name"
    assert conductor_workflow.name == "new_name"


def test_name_property_invalid_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.name = 123


def test_version_property(conductor_workflow):
    conductor_workflow.version = 2
    assert conductor_workflow.version == 2


def test_version_property_none(conductor_workflow):
    conductor_workflow.version = None
    assert conductor_workflow.version is None


def test_version_property_invalid_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.version = "invalid"


def test_description_property(conductor_workflow):
    conductor_workflow.description = "New description"
    assert conductor_workflow.description == "New description"


def test_description_property_none(conductor_workflow):
    conductor_workflow.description = None
    assert conductor_workflow.description is None


def test_description_property_invalid_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.description = 123


def test_timeout_policy(conductor_workflow):
    result = conductor_workflow.timeout_policy(TimeoutPolicy.TIME_OUT_WORKFLOW)
    assert conductor_workflow._timeout_policy == TimeoutPolicy.TIME_OUT_WORKFLOW
    assert result == conductor_workflow


def test_timeout_policy_invalid_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.timeout_policy("invalid")


def test_timeout_seconds(conductor_workflow):
    result = conductor_workflow.timeout_seconds(120)
    assert conductor_workflow._timeout_seconds == 120
    assert result == conductor_workflow


def test_timeout_seconds_invalid_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.timeout_seconds("invalid")


def test_owner_email(conductor_workflow):
    result = conductor_workflow.owner_email("test@example.com")
    assert conductor_workflow._owner_email == "test@example.com"
    assert result == conductor_workflow


def test_owner_email_invalid_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.owner_email(123)


def test_failure_workflow(conductor_workflow):
    result = conductor_workflow.failure_workflow("failure_workflow")
    assert conductor_workflow._failure_workflow == "failure_workflow"
    assert result == conductor_workflow


def test_failure_workflow_invalid_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.failure_workflow(123)


def test_restartable(conductor_workflow):
    result = conductor_workflow.restartable(False)
    assert conductor_workflow._restartable is False
    assert result == conductor_workflow


def test_restartable_invalid_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.restartable("invalid")


def test_enable_status_listener(conductor_workflow):
    conductor_workflow.enable_status_listener("test_sink")
    assert conductor_workflow._workflow_status_listener_enabled is True
    assert conductor_workflow._workflow_status_listener_sink == "test_sink"


def test_disable_status_listener(conductor_workflow):
    conductor_workflow.enable_status_listener("test_sink")
    conductor_workflow.disable_status_listener()
    assert conductor_workflow._workflow_status_listener_enabled is False
    assert conductor_workflow._workflow_status_listener_sink is None


def test_output_parameters(conductor_workflow):
    output_params = {"key1": "value1", "key2": "value2"}
    result = conductor_workflow.output_parameters(output_params)
    assert conductor_workflow._output_parameters == output_params
    assert result == conductor_workflow


def test_output_parameters_none(conductor_workflow):
    result = conductor_workflow.output_parameters(None)
    assert conductor_workflow._output_parameters == {}
    assert result is None


def test_output_parameters_invalid_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.output_parameters("invalid")


def test_output_parameters_invalid_key_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.output_parameters({123: "value"})


def test_output_parameter(conductor_workflow):
    result = conductor_workflow.output_parameter("key1", "value1")
    assert conductor_workflow._output_parameters["key1"] == "value1"
    assert result == conductor_workflow


def test_output_parameter_with_none_output_parameters(conductor_workflow):
    conductor_workflow._output_parameters = None
    result = conductor_workflow.output_parameter("key1", "value1")
    assert conductor_workflow._output_parameters["key1"] == "value1"
    assert result == conductor_workflow


def test_input_template(conductor_workflow):
    input_template = {"param1": "${workflow.input.value1}"}
    result = conductor_workflow.input_template(input_template)
    assert conductor_workflow._input_template == input_template
    assert result == conductor_workflow


def test_input_template_none(conductor_workflow):
    result = conductor_workflow.input_template(None)
    assert conductor_workflow._input_template == {}
    assert result is None


def test_input_template_invalid_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.input_template("invalid")


def test_input_template_invalid_key_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.input_template({123: "value"})


def test_variables(conductor_workflow):
    variables = {"var1": "value1", "var2": "value2"}
    result = conductor_workflow.variables(variables)
    assert conductor_workflow._variables == variables
    assert result == conductor_workflow


def test_variables_none(conductor_workflow):
    result = conductor_workflow.variables(None)
    assert conductor_workflow._variables == {}
    assert result is None


def test_variables_invalid_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.variables("invalid")


def test_variables_invalid_key_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.variables({123: "value"})


def test_input_parameters_list(conductor_workflow):
    input_params = ["param1", "param2"]
    result = conductor_workflow.input_parameters(input_params)
    assert conductor_workflow._input_parameters == input_params
    assert result == conductor_workflow


def test_input_parameters_dict(conductor_workflow):
    input_params = {"param1": "value1"}
    result = conductor_workflow.input_parameters(input_params)
    assert conductor_workflow._input_template == input_params
    assert result == conductor_workflow


def test_input_parameters_invalid_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.input_parameters(123)


def test_input_parameters_invalid_item_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow.input_parameters(["param1", 123])


def test_workflow_input(conductor_workflow):
    input_data = {"param1": "value1"}
    result = conductor_workflow.workflow_input(input_data)
    assert conductor_workflow._input_template == input_data
    assert result == conductor_workflow


@pytest.mark.asyncio
async def test_register(conductor_workflow, mock_executor):
    mock_executor.register_workflow.return_value = {"status": "success"}

    result = await conductor_workflow.register(overwrite=True)

    mock_executor.register_workflow.assert_called_once()
    call_args = mock_executor.register_workflow.call_args
    assert call_args[1]["overwrite"] is True
    assert call_args[1]["workflow"] is not None
    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_start_workflow(conductor_workflow, mock_executor):
    mock_executor.start_workflow.return_value = "workflow_id_123"
    start_request = StartWorkflowRequestAdapter(name="test")

    result = await conductor_workflow.start_workflow(start_request)

    mock_executor.start_workflow.assert_called_once_with(start_request)
    assert start_request.workflow_def is not None
    assert start_request.name == "test_workflow"
    assert start_request.version == 1
    assert result == "workflow_id_123"


@pytest.mark.asyncio
async def test_start_workflow_with_input(conductor_workflow, mock_executor):
    mock_executor.start_workflow.return_value = "workflow_id_123"

    with patch('conductor.asyncio_client.workflow.conductor_workflow.StartWorkflowRequestAdapter') as mock_request_class:
        mock_request = MagicMock()
        mock_request_class.return_value = mock_request

        result = await conductor_workflow.start_workflow_with_input(
            workflow_input={"param1": "value1"},
            correlation_id="test_correlation",
            task_to_domain={"task1": "domain1"},
            priority=1,
            idempotency_key="key123",
            idempotency_strategy=IdempotencyStrategy.FAIL
        )

        mock_executor.start_workflow.assert_called_once_with(mock_request)
        assert result == "workflow_id_123"


@pytest.mark.asyncio
async def test_start_workflow_with_input_defaults(conductor_workflow, mock_executor):
    mock_executor.start_workflow.return_value = "workflow_id_123"

    with patch('conductor.asyncio_client.workflow.conductor_workflow.StartWorkflowRequestAdapter') as mock_request_class:
        mock_request = MagicMock()
        mock_request_class.return_value = mock_request

        result = await conductor_workflow.start_workflow_with_input()

        mock_executor.start_workflow.assert_called_once_with(mock_request)
        assert result == "workflow_id_123"


@pytest.mark.asyncio
async def test_execute(conductor_workflow, mock_executor, mock_workflow_run):
    mock_executor.execute_workflow.return_value = mock_workflow_run

    with patch('conductor.asyncio_client.workflow.conductor_workflow.StartWorkflowRequestAdapter') as mock_request_class:
        mock_request = MagicMock()
        mock_request_class.return_value = mock_request

        result = await conductor_workflow.execute(
            workflow_input={"param1": "value1"},
            wait_until_task_ref="task1",
            wait_for_seconds=30,
            request_id="custom_request_id",
            idempotency_key="key123",
            idempotency_strategy=IdempotencyStrategy.FAIL,
            task_to_domain={"task1": "domain1"}
        )

        mock_executor.execute_workflow.assert_called_once()
        call_args = mock_executor.execute_workflow.call_args
        assert call_args[1]["wait_until_task_ref"] == "task1"
        assert call_args[1]["wait_for_seconds"] == 30
        assert call_args[1]["request_id"] == "custom_request_id"
        assert result == mock_workflow_run


@pytest.mark.asyncio
async def test_execute_defaults(conductor_workflow, mock_executor, mock_workflow_run):
    mock_executor.execute_workflow.return_value = mock_workflow_run

    with patch('conductor.asyncio_client.workflow.conductor_workflow.StartWorkflowRequestAdapter') as mock_request_class:
        mock_request = MagicMock()
        mock_request_class.return_value = mock_request

        result = await conductor_workflow.execute()

        mock_executor.execute_workflow.assert_called_once()
        call_args = mock_executor.execute_workflow.call_args
        assert call_args[1]["wait_until_task_ref"] == ""
        assert call_args[1]["wait_for_seconds"] == 10
        assert result == mock_workflow_run


def test_to_workflow_def(conductor_workflow):
    with patch('conductor.asyncio_client.workflow.conductor_workflow.WorkflowDefAdapter') as mock_def_class:
        mock_def = MagicMock(spec=WorkflowDefAdapter)
        mock_def_class.return_value = mock_def

        result = conductor_workflow.to_workflow_def()

        mock_def_class.assert_called_once()
        call_args = mock_def_class.call_args
        assert call_args[1]["name"] == "test_workflow"
        assert call_args[1]["description"] == "Test workflow"
        assert call_args[1]["version"] == 1
        assert call_args[1]["schema_version"] == 2
        assert result == mock_def


def test_to_workflow_task(conductor_workflow):
    with patch('conductor.asyncio_client.workflow.conductor_workflow.InlineSubWorkflowTask') as mock_task_class:
        mock_task = MagicMock()
        mock_task.to_workflow_task.return_value = MagicMock(spec=WorkflowTaskAdapter)
        mock_task_class.return_value = mock_task

        result = conductor_workflow.to_workflow_task()

        mock_task_class.assert_called_once()
        assert result is not None


def test_get_workflow_task_list_empty(conductor_workflow):
    result = conductor_workflow._AsyncConductorWorkflow__get_workflow_task_list()
    assert result == []


def test_get_workflow_task_list_single_task(conductor_workflow, mock_task):
    conductor_workflow._tasks = [mock_task]

    result = conductor_workflow._AsyncConductorWorkflow__get_workflow_task_list()

    assert len(result) == 1
    assert result[0] == mock_task._mock_workflow_task


def test_get_workflow_task_list_multiple_tasks(conductor_workflow, mock_task):
    class MockTask2(TaskInterface):
        def __init__(self):
            super().__init__("test_task2", TaskType.SIMPLE)
            self._mock_workflow_task = MagicMock(spec=WorkflowTaskAdapter)
            self._mock_workflow_task.type = "SIMPLE"

        def to_workflow_task(self):
            return self._mock_workflow_task

    mock_task2 = MockTask2()
    conductor_workflow._tasks = [mock_task, mock_task2]

    result = conductor_workflow._AsyncConductorWorkflow__get_workflow_task_list()

    assert len(result) == 2
    assert result[0] == mock_task._mock_workflow_task
    assert result[1] == mock_task2._mock_workflow_task


def test_rshift_single_task(conductor_workflow, mock_task):
    result = conductor_workflow.__rshift__(mock_task)

    assert result == conductor_workflow
    assert len(conductor_workflow._tasks) == 1
    assert conductor_workflow._tasks[0] is not None


def test_rshift_list_tasks(conductor_workflow, mock_task):
    class MockTask2(TaskInterface):
        def __init__(self):
            super().__init__("test_task2", TaskType.SIMPLE)

    mock_task2 = MockTask2()

    result = conductor_workflow.__rshift__([mock_task, mock_task2])

    assert result == conductor_workflow
    assert len(conductor_workflow._tasks) == 1


def test_rshift_fork_join_tasks(conductor_workflow, mock_task):
    class MockTask2(TaskInterface):
        def __init__(self):
            super().__init__("test_task2", TaskType.SIMPLE)

    mock_task2 = MockTask2()

    with patch('conductor.asyncio_client.workflow.conductor_workflow.ForkTask') as mock_fork_class:
        mock_fork_task = MagicMock()
        mock_fork_class.return_value = mock_fork_task

        result = conductor_workflow.__rshift__([[mock_task], [mock_task2]])

        assert result == conductor_workflow
        mock_fork_class.assert_called_once()


def test_rshift_workflow(conductor_workflow):
    sub_workflow = AsyncConductorWorkflow(MagicMock(), "sub_workflow", 1)

    with patch('conductor.asyncio_client.workflow.conductor_workflow.InlineSubWorkflowTask') as mock_inline_class:
        class MockInlineTask(TaskInterface):
            def __init__(self):
                super().__init__("mock_inline", TaskType.SUB_WORKFLOW)

        mock_inline_task = MockInlineTask()
        mock_inline_class.return_value = mock_inline_task

        result = conductor_workflow.__rshift__(sub_workflow)

        assert result == conductor_workflow
        mock_inline_class.assert_called_once()


def test_add_single_task(conductor_workflow, mock_task):
    result = conductor_workflow.add(mock_task)

    assert result == conductor_workflow
    assert len(conductor_workflow._tasks) == 1
    assert conductor_workflow._tasks[0] is not None


def test_add_list_tasks(conductor_workflow, mock_task):
    class MockTask2(TaskInterface):
        def __init__(self):
            super().__init__("test_task2", TaskType.SIMPLE)

    mock_task2 = MockTask2()

    result = conductor_workflow.add([mock_task, mock_task2])

    assert result == conductor_workflow
    assert len(conductor_workflow._tasks) == 2


def test_add_task_invalid_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid task"):
        conductor_workflow.add("invalid_task")


def test_add_fork_join_tasks(conductor_workflow, mock_task):
    class MockTask2(TaskInterface):
        def __init__(self):
            super().__init__("test_task2", TaskType.SIMPLE)

    mock_task2 = MockTask2()

    with patch('conductor.asyncio_client.workflow.conductor_workflow.ForkTask') as mock_fork_class:
        mock_fork_task = MagicMock()
        mock_fork_class.return_value = mock_fork_task

        conductor_workflow._AsyncConductorWorkflow__add_fork_join_tasks([[mock_task], [mock_task2]])

        mock_fork_class.assert_called_once()
        assert len(conductor_workflow._tasks) == 1
        assert conductor_workflow._tasks[0] == mock_fork_task


def test_add_fork_join_tasks_invalid_type(conductor_workflow):
    with pytest.raises(Exception, match="Invalid type"):
        conductor_workflow._AsyncConductorWorkflow__add_fork_join_tasks([["invalid_task"]])


@pytest.mark.asyncio
async def test_call(conductor_workflow, mock_executor, mock_workflow_run):
    mock_executor.execute_workflow.return_value = mock_workflow_run

    with patch('conductor.asyncio_client.workflow.conductor_workflow.StartWorkflowRequestAdapter') as mock_request_class:
        mock_request = MagicMock()
        mock_request_class.return_value = mock_request

        result = await conductor_workflow(param1="value1", param2="value2")

        mock_executor.execute_workflow.assert_called_once()
        assert result == mock_workflow_run


@pytest.mark.asyncio
async def test_call_no_params(conductor_workflow, mock_executor, mock_workflow_run):
    mock_executor.execute_workflow.return_value = mock_workflow_run

    with patch('conductor.asyncio_client.workflow.conductor_workflow.StartWorkflowRequestAdapter') as mock_request_class:
        mock_request = MagicMock()
        mock_request_class.return_value = mock_request

        result = await conductor_workflow()

        mock_executor.execute_workflow.assert_called_once()
        assert result == mock_workflow_run


def test_input(conductor_workflow):
    result = conductor_workflow.input("param1")
    assert result == "${workflow.input.param1}"


def test_input_none(conductor_workflow):
    result = conductor_workflow.input(None)
    assert result == "${workflow.input}"


def test_output(conductor_workflow):
    result = conductor_workflow.output("result1")
    assert result == "${workflow.output.result1}"


def test_output_none(conductor_workflow):
    result = conductor_workflow.output(None)
    assert result == "${workflow.output}"


def test_inline_sub_workflow_task_init():
    workflow = AsyncConductorWorkflow(MagicMock(), "test_workflow", 1)
    task = InlineSubWorkflowTask("task_ref", workflow)

    assert task.task_reference_name == "task_ref"
    assert task.task_type == TaskType.SUB_WORKFLOW
    assert task._workflow_name == "test_workflow"
    assert task._workflow_version == 1


def test_inline_sub_workflow_task_to_workflow_task():
    workflow = AsyncConductorWorkflow(MagicMock(), "test_workflow", 1)
    task = InlineSubWorkflowTask("task_ref", workflow)

    with patch('conductor.asyncio_client.workflow.conductor_workflow.SubWorkflowParamsAdapter') as mock_params_class:
        mock_params = MagicMock()
        mock_params_class.return_value = mock_params

        with patch('conductor.asyncio_client.workflow.task.task.TaskInterface.to_workflow_task') as mock_super:
            mock_super.return_value = MagicMock()
            result = task.to_workflow_task()

            mock_params_class.assert_called_once()
            call_args = mock_params_class.call_args
            assert call_args[1]["name"] == "test_workflow"
            assert call_args[1]["version"] == 1
            assert result is not None
