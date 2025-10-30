import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from conductor.asyncio_client.adapters.models.extended_workflow_def_adapter import ExtendedWorkflowDefAdapter
from conductor.asyncio_client.adapters.models.rerun_workflow_request_adapter import RerunWorkflowRequestAdapter
from conductor.asyncio_client.adapters.models.scrollable_search_result_workflow_summary_adapter import ScrollableSearchResultWorkflowSummaryAdapter
from conductor.asyncio_client.adapters.models.skip_task_request_adapter import SkipTaskRequestAdapter
from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import StartWorkflowRequestAdapter
from conductor.asyncio_client.adapters.models.task_result_adapter import TaskResultAdapter
from conductor.asyncio_client.adapters.models.workflow_adapter import WorkflowAdapter
from conductor.asyncio_client.adapters.models.workflow_run_adapter import WorkflowRunAdapter
from conductor.asyncio_client.adapters.models.workflow_status_adapter import WorkflowStatusAdapter
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.workflow.executor.workflow_executor import AsyncWorkflowExecutor


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def mock_configuration():
    return Configuration("http://localhost:8080/api")


@pytest.fixture
def mock_metadata_client():
    return AsyncMock()


@pytest.fixture
def mock_task_client():
    return AsyncMock()


@pytest.fixture
def mock_workflow_client():
    return AsyncMock()


@pytest.fixture
def workflow_executor(mock_configuration, mock_metadata_client, mock_task_client, mock_workflow_client):
    with patch('conductor.asyncio_client.workflow.executor.workflow_executor.ApiClient') as mock_api_client, \
         patch('conductor.asyncio_client.workflow.executor.workflow_executor.MetadataResourceApiAdapter', return_value=mock_metadata_client), \
         patch('conductor.asyncio_client.workflow.executor.workflow_executor.TaskResourceApiAdapter', return_value=mock_task_client), \
         patch('conductor.asyncio_client.workflow.executor.workflow_executor.OrkesWorkflowClient', return_value=mock_workflow_client):

        api_client = ApiClient(mock_configuration)
        executor = AsyncWorkflowExecutor(mock_configuration, api_client=api_client)
        executor.metadata_client = mock_metadata_client
        executor.task_client = mock_task_client
        executor.workflow_client = mock_workflow_client
        return executor


@pytest.fixture
def start_workflow_request():
    request = StartWorkflowRequestAdapter(name="test_workflow")
    request.version = 1
    request.input = {"param1": "value1"}
    request.correlation_id = "test_correlation"
    return request


@pytest.fixture
def workflow_def():
    workflow = MagicMock(spec=ExtendedWorkflowDefAdapter)
    workflow.name = "test_workflow"
    workflow.version = 1
    return workflow


@pytest.mark.asyncio
async def test_init(workflow_executor, mock_metadata_client, mock_task_client, mock_workflow_client):
    assert workflow_executor.metadata_client == mock_metadata_client
    assert workflow_executor.task_client == mock_task_client
    assert workflow_executor.workflow_client == mock_workflow_client


@pytest.mark.asyncio
async def test_register_workflow(workflow_executor, mock_metadata_client, workflow_def):
    mock_metadata_client.update.return_value = {"status": "success"}

    result = await workflow_executor.register_workflow(workflow_def, overwrite=True)

    mock_metadata_client.update.assert_called_once_with(
        extended_workflow_def=[workflow_def], overwrite=True
    )
    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_register_workflow_without_overwrite(workflow_executor, mock_metadata_client, workflow_def):
    mock_metadata_client.update.return_value = {"status": "success"}

    result = await workflow_executor.register_workflow(workflow_def)

    mock_metadata_client.update.assert_called_once_with(
        extended_workflow_def=[workflow_def], overwrite=None
    )
    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_start_workflow(workflow_executor, mock_workflow_client, start_workflow_request):
    mock_workflow_client.start_workflow.return_value = "workflow_id_123"

    result = await workflow_executor.start_workflow(start_workflow_request)

    mock_workflow_client.start_workflow.assert_called_once_with(
        start_workflow_request=start_workflow_request
    )
    assert result == "workflow_id_123"


@pytest.mark.asyncio
async def test_start_workflows(workflow_executor, mock_workflow_client, start_workflow_request):
    request1 = StartWorkflowRequestAdapter(name="workflow1")
    request2 = StartWorkflowRequestAdapter(name="workflow2")

    mock_workflow_client.start_workflow.side_effect = ["id1", "id2"]

    result = await workflow_executor.start_workflows(request1, request2)

    assert mock_workflow_client.start_workflow.call_count == 2
    assert result == ["id1", "id2"]


@pytest.mark.asyncio
async def test_execute_workflow(workflow_executor, mock_workflow_client, start_workflow_request):
    mock_workflow_run = MagicMock(spec=WorkflowRunAdapter)
    mock_workflow_client.execute_workflow.return_value = mock_workflow_run

    result = await workflow_executor.execute_workflow(
        start_workflow_request,
        wait_until_task_ref="task1",
        wait_for_seconds=30,
        request_id="custom_request_id"
    )

    mock_workflow_client.execute_workflow.assert_called_once_with(
        start_workflow_request=start_workflow_request,
        request_id="custom_request_id",
        wait_until_task_ref="task1",
        wait_for_seconds=30
    )
    assert result == mock_workflow_run


@pytest.mark.asyncio
async def test_execute_workflow_with_defaults(workflow_executor, mock_workflow_client, start_workflow_request):
    mock_workflow_run = MagicMock(spec=WorkflowRunAdapter)
    mock_workflow_client.execute_workflow.return_value = mock_workflow_run

    result = await workflow_executor.execute_workflow(start_workflow_request)

    mock_workflow_client.execute_workflow.assert_called_once()
    call_args = mock_workflow_client.execute_workflow.call_args
    assert call_args[1]["start_workflow_request"] == start_workflow_request
    assert call_args[1]["wait_until_task_ref"] is None
    assert call_args[1]["wait_for_seconds"] == 10
    assert result == mock_workflow_run


@pytest.mark.asyncio
async def test_execute_workflow_with_return_strategy(workflow_executor, mock_workflow_client, start_workflow_request):
    mock_workflow_run = MagicMock(spec=WorkflowRunAdapter)
    mock_workflow_client.execute_workflow_with_return_strategy.return_value = mock_workflow_run

    result = await workflow_executor.execute_workflow_with_return_strategy(
        start_workflow_request,
        wait_until_task_ref="task1",
        wait_for_seconds=30,
        request_id="custom_request_id"
    )

    mock_workflow_client.execute_workflow_with_return_strategy.assert_called_once_with(
        start_workflow_request=start_workflow_request,
        request_id="custom_request_id",
        wait_until_task_ref="task1",
        wait_for_seconds=30
    )
    assert result == mock_workflow_run


@pytest.mark.asyncio
async def test_execute(workflow_executor, mock_workflow_client):
    mock_workflow_run = MagicMock(spec=WorkflowRunAdapter)
    mock_workflow_client.execute_workflow.return_value = mock_workflow_run

    with patch('conductor.asyncio_client.workflow.executor.workflow_executor.StartWorkflowRequestAdapter') as mock_request_class:
        mock_request = MagicMock()
        mock_request_class.return_value = mock_request

        result = await workflow_executor.execute(
            name="test_workflow",
            version=2,
            workflow_input={"param1": "value1"},
            wait_until_task_ref="task1",
            wait_for_seconds=30,
            request_id="custom_request_id",
            correlation_id="test_correlation",
            domain="test_domain"
        )

        mock_workflow_client.execute_workflow.assert_called_once()
        call_args = mock_workflow_client.execute_workflow.call_args
        start_request = call_args[1]["start_workflow_request"]
        assert start_request == mock_request
        assert result == mock_workflow_run


@pytest.mark.asyncio
async def test_execute_with_defaults(workflow_executor, mock_workflow_client):
    mock_workflow_run = MagicMock(spec=WorkflowRunAdapter)
    mock_workflow_client.execute_workflow.return_value = mock_workflow_run

    with patch('conductor.asyncio_client.workflow.executor.workflow_executor.StartWorkflowRequestAdapter') as mock_request_class:
        mock_request = MagicMock()
        mock_request_class.return_value = mock_request

        result = await workflow_executor.execute("test_workflow")

        mock_workflow_client.execute_workflow.assert_called_once()
        call_args = mock_workflow_client.execute_workflow.call_args
        start_request = call_args[1]["start_workflow_request"]
        assert start_request == mock_request
        assert result == mock_workflow_run


@pytest.mark.asyncio
async def test_remove_workflow(workflow_executor, mock_workflow_client):
    await workflow_executor.remove_workflow("workflow_id_123", archive_workflow=True)

    mock_workflow_client.delete_workflow.assert_called_once_with(
        workflow_id="workflow_id_123", archive_workflow=True
    )


@pytest.mark.asyncio
async def test_remove_workflow_without_archive(workflow_executor, mock_workflow_client):
    await workflow_executor.remove_workflow("workflow_id_123")

    mock_workflow_client.delete_workflow.assert_called_once_with(
        workflow_id="workflow_id_123"
    )


@pytest.mark.asyncio
async def test_get_workflow(workflow_executor, mock_workflow_client):
    mock_workflow = MagicMock(spec=WorkflowAdapter)
    mock_workflow_client.get_workflow.return_value = mock_workflow

    result = await workflow_executor.get_workflow("workflow_id_123", include_tasks=True)

    mock_workflow_client.get_workflow.assert_called_once_with(
        workflow_id="workflow_id_123", include_tasks=True
    )
    assert result == mock_workflow


@pytest.mark.asyncio
async def test_get_workflow_without_include_tasks(workflow_executor, mock_workflow_client):
    mock_workflow = MagicMock(spec=WorkflowAdapter)
    mock_workflow_client.get_workflow.return_value = mock_workflow

    result = await workflow_executor.get_workflow("workflow_id_123")

    mock_workflow_client.get_workflow.assert_called_once_with(
        workflow_id="workflow_id_123"
    )
    assert result == mock_workflow


@pytest.mark.asyncio
async def test_get_workflow_status(workflow_executor, mock_workflow_client):
    mock_status = MagicMock(spec=WorkflowStatusAdapter)
    mock_workflow_client.get_workflow_status.return_value = mock_status

    result = await workflow_executor.get_workflow_status(
        "workflow_id_123", include_output=True, include_variables=True
    )

    mock_workflow_client.get_workflow_status.assert_called_once_with(
        workflow_id="workflow_id_123",
        include_output=True,
        include_variables=True
    )
    assert result == mock_status


@pytest.mark.asyncio
async def test_get_workflow_status_without_options(workflow_executor, mock_workflow_client):
    mock_status = MagicMock(spec=WorkflowStatusAdapter)
    mock_workflow_client.get_workflow_status.return_value = mock_status

    result = await workflow_executor.get_workflow_status("workflow_id_123")

    mock_workflow_client.get_workflow_status.assert_called_once_with(
        workflow_id="workflow_id_123",
        include_output=None,
        include_variables=None
    )
    assert result == mock_status


@pytest.mark.asyncio
async def test_search(workflow_executor, mock_workflow_client):
    mock_search_result = MagicMock(spec=ScrollableSearchResultWorkflowSummaryAdapter)
    mock_workflow_client.search.return_value = mock_search_result

    result = await workflow_executor.search(
        start=0,
        size=10,
        free_text="test",
        query="status:COMPLETED",
        skip_cache=True
    )

    mock_workflow_client.search.assert_called_once_with(
        start=0,
        size=10,
        free_text="test",
        query="status:COMPLETED",
        skip_cache=True
    )
    assert result == mock_search_result


@pytest.mark.asyncio
async def test_search_with_defaults(workflow_executor, mock_workflow_client):
    mock_search_result = MagicMock(spec=ScrollableSearchResultWorkflowSummaryAdapter)
    mock_workflow_client.search.return_value = mock_search_result

    result = await workflow_executor.search()

    mock_workflow_client.search.assert_called_once_with(
        start=None,
        size=None,
        free_text=None,
        query=None,
        skip_cache=None
    )
    assert result == mock_search_result


@pytest.mark.asyncio
async def test_get_by_correlation_ids(workflow_executor, mock_workflow_client):
    mock_workflows = [MagicMock(spec=WorkflowAdapter)]
    mock_workflow_client.get_by_correlation_ids.return_value = {"correlation1": mock_workflows}

    result = await workflow_executor.get_by_correlation_ids(
        "test_workflow",
        ["correlation1", "correlation2"],
        include_closed=True,
        include_tasks=True
    )

    mock_workflow_client.get_by_correlation_ids.assert_called_once_with(
        correlation_ids=["correlation1", "correlation2"],
        workflow_name="test_workflow",
        include_tasks=True,
        include_completed=True
    )
    assert result == {"correlation1": mock_workflows}


@pytest.mark.asyncio
async def test_get_by_correlation_ids_and_names(workflow_executor, mock_workflow_client):
    mock_batch_request = MagicMock()
    mock_workflows = [MagicMock(spec=WorkflowAdapter)]
    mock_workflow_client.get_by_correlation_ids_in_batch.return_value = {"correlation1": mock_workflows}

    result = await workflow_executor.get_by_correlation_ids_and_names(
        mock_batch_request,
        include_closed=True,
        include_tasks=True
    )

    mock_workflow_client.get_by_correlation_ids_in_batch.assert_called_once_with(
        batch_request=mock_batch_request,
        include_completed=True,
        include_tasks=True
    )
    assert result == {"correlation1": mock_workflows}


@pytest.mark.asyncio
async def test_pause(workflow_executor, mock_workflow_client):
    await workflow_executor.pause("workflow_id_123")

    mock_workflow_client.pause_workflow.assert_called_once_with(
        workflow_id="workflow_id_123"
    )


@pytest.mark.asyncio
async def test_resume(workflow_executor, mock_workflow_client):
    await workflow_executor.resume("workflow_id_123")

    mock_workflow_client.resume_workflow.assert_called_once_with(
        workflow_id="workflow_id_123"
    )


@pytest.mark.asyncio
async def test_terminate(workflow_executor, mock_workflow_client):
    await workflow_executor.terminate(
        "workflow_id_123",
        reason="Test termination",
        trigger_failure_workflow=True
    )

    mock_workflow_client.terminate_workflow.assert_called_once_with(
        workflow_id="workflow_id_123",
        reason="Test termination",
        trigger_failure_workflow=True
    )


@pytest.mark.asyncio
async def test_terminate_without_options(workflow_executor, mock_workflow_client):
    await workflow_executor.terminate("workflow_id_123")

    mock_workflow_client.terminate_workflow.assert_called_once_with(
        workflow_id="workflow_id_123",
        reason=None,
        trigger_failure_workflow=None
    )


@pytest.mark.asyncio
async def test_restart(workflow_executor, mock_workflow_client):
    await workflow_executor.restart("workflow_id_123", use_latest_definitions=True)

    mock_workflow_client.restart_workflow.assert_called_once_with(
        workflow_id="workflow_id_123",
        use_latest_definitions=True
    )


@pytest.mark.asyncio
async def test_restart_without_options(workflow_executor, mock_workflow_client):
    await workflow_executor.restart("workflow_id_123")

    mock_workflow_client.restart_workflow.assert_called_once_with(
        workflow_id="workflow_id_123",
        use_latest_definitions=None
    )


@pytest.mark.asyncio
async def test_retry(workflow_executor, mock_workflow_client):
    await workflow_executor.retry("workflow_id_123", resume_subworkflow_tasks=True)

    mock_workflow_client.retry_workflow.assert_called_once_with(
        workflow_id="workflow_id_123",
        resume_subworkflow_tasks=True
    )


@pytest.mark.asyncio
async def test_retry_without_options(workflow_executor, mock_workflow_client):
    await workflow_executor.retry("workflow_id_123")

    mock_workflow_client.retry_workflow.assert_called_once_with(
        workflow_id="workflow_id_123",
        resume_subworkflow_tasks=None
    )


@pytest.mark.asyncio
async def test_rerun(workflow_executor, mock_workflow_client):
    mock_rerun_request = MagicMock(spec=RerunWorkflowRequestAdapter)
    mock_workflow_client.rerun_workflow.return_value = "new_workflow_id"

    result = await workflow_executor.rerun(mock_rerun_request, "workflow_id_123")

    mock_workflow_client.rerun_workflow.assert_called_once_with(
        rerun_workflow_request=mock_rerun_request,
        workflow_id="workflow_id_123"
    )
    assert result == "new_workflow_id"


@pytest.mark.asyncio
async def test_skip_task_from_workflow(workflow_executor, mock_workflow_client):
    mock_skip_request = MagicMock(spec=SkipTaskRequestAdapter)

    await workflow_executor.skip_task_from_workflow(
        "workflow_id_123",
        "task_ref_name",
        mock_skip_request
    )

    mock_workflow_client.skip_task_from_workflow.assert_called_once_with(
        workflow_id="workflow_id_123",
        task_reference_name="task_ref_name",
        skip_task_request=mock_skip_request
    )


@pytest.mark.asyncio
async def test_skip_task_from_workflow_without_request(workflow_executor, mock_workflow_client):
    await workflow_executor.skip_task_from_workflow("workflow_id_123", "task_ref_name")

    mock_workflow_client.skip_task_from_workflow.assert_called_once_with(
        workflow_id="workflow_id_123",
        task_reference_name="task_ref_name",
        skip_task_request=None
    )


@pytest.mark.asyncio
async def test_update_task(workflow_executor, mock_task_client):
    mock_task_client.update_task.return_value = "task_id_123"

    result = await workflow_executor.update_task(
        "task_id_123",
        "workflow_id_123",
        {"output": "result"},
        "COMPLETED"
    )

    mock_task_client.update_task.assert_called_once()
    call_args = mock_task_client.update_task.call_args
    task_result = call_args[1]["task_result"]
    assert task_result.task_id == "task_id_123"
    assert task_result.workflow_instance_id == "workflow_id_123"
    assert task_result.output_data == {"output": "result"}
    assert task_result.status == "COMPLETED"
    assert result == "task_id_123"


@pytest.mark.asyncio
async def test_update_task_by_ref_name(workflow_executor, mock_task_client):
    mock_task_client.update_task1.return_value = "task_id_123"

    result = await workflow_executor.update_task_by_ref_name(
        {"output": "result"},
        "workflow_id_123",
        "task_ref_name",
        "COMPLETED"
    )

    mock_task_client.update_task1.assert_called_once_with(
        request_body={"output": "result"},
        workflow_id="workflow_id_123",
        task_ref_name="task_ref_name",
        status="COMPLETED"
    )
    assert result == "task_id_123"


@pytest.mark.asyncio
async def test_update_task_by_ref_name_sync(workflow_executor, mock_task_client):
    mock_workflow = MagicMock(spec=WorkflowAdapter)
    mock_task_client.update_task_sync.return_value = mock_workflow

    result = await workflow_executor.update_task_by_ref_name_sync(
        {"output": "result"},
        "workflow_id_123",
        "task_ref_name",
        "COMPLETED"
    )

    mock_task_client.update_task_sync.assert_called_once_with(
        request_body={"output": "result"},
        workflow_id="workflow_id_123",
        task_ref_name="task_ref_name",
        status="COMPLETED"
    )
    assert result == mock_workflow


@pytest.mark.asyncio
async def test_get_task(workflow_executor, mock_task_client):
    mock_task_client.get_task.return_value = "task_data"

    result = await workflow_executor.get_task("task_id_123")

    mock_task_client.get_task.assert_called_once_with(task_id="task_id_123")
    assert result == "task_data"


def test_get_task_result(workflow_executor):
    result = workflow_executor._AsyncWorkflowExecutor__get_task_result(
        "task_id_123",
        "workflow_id_123",
        {"output": "result"},
        "COMPLETED"
    )

    assert isinstance(result, TaskResultAdapter)
    assert result.task_id == "task_id_123"
    assert result.workflow_instance_id == "workflow_id_123"
    assert result.output_data == {"output": "result"}
    assert result.status == "COMPLETED"


@pytest.mark.asyncio
async def test_execute_workflow_with_uuid_generation(workflow_executor, mock_workflow_client, start_workflow_request):
    mock_workflow_run = MagicMock(spec=WorkflowRunAdapter)
    mock_workflow_client.execute_workflow.return_value = mock_workflow_run

    result = await workflow_executor.execute_workflow(start_workflow_request)

    call_args = mock_workflow_client.execute_workflow.call_args
    request_id = call_args[1]["request_id"]
    assert request_id is not None
    assert len(request_id) > 0


@pytest.mark.asyncio
async def test_execute_workflow_with_return_strategy_uuid_generation(workflow_executor, mock_workflow_client, start_workflow_request):
    mock_workflow_run = MagicMock(spec=WorkflowRunAdapter)
    mock_workflow_client.execute_workflow_with_return_strategy.return_value = mock_workflow_run

    result = await workflow_executor.execute_workflow_with_return_strategy(start_workflow_request)

    call_args = mock_workflow_client.execute_workflow_with_return_strategy.call_args
    request_id = call_args[1]["request_id"]
    assert request_id is not None
    assert len(request_id) > 0


@pytest.mark.asyncio
async def test_execute_with_uuid_generation(workflow_executor, mock_workflow_client):
    mock_workflow_run = MagicMock(spec=WorkflowRunAdapter)
    mock_workflow_client.execute_workflow.return_value = mock_workflow_run

    with patch('conductor.asyncio_client.workflow.executor.workflow_executor.StartWorkflowRequestAdapter') as mock_request_class:
        mock_request = MagicMock()
        mock_request_class.return_value = mock_request

        result = await workflow_executor.execute("test_workflow")

        call_args = mock_workflow_client.execute_workflow.call_args
        request_id = call_args[1]["request_id"]
        assert request_id is not None
        assert len(request_id) > 0


@pytest.mark.asyncio
async def test_execute_with_custom_request_id(workflow_executor, mock_workflow_client):
    mock_workflow_run = MagicMock(spec=WorkflowRunAdapter)
    mock_workflow_client.execute_workflow.return_value = mock_workflow_run

    with patch('conductor.asyncio_client.workflow.executor.workflow_executor.StartWorkflowRequestAdapter') as mock_request_class:
        mock_request = MagicMock()
        mock_request_class.return_value = mock_request

        result = await workflow_executor.execute("test_workflow", request_id="custom_id")

        call_args = mock_workflow_client.execute_workflow.call_args
        request_id = call_args[1]["request_id"]
        assert request_id == "custom_id"
