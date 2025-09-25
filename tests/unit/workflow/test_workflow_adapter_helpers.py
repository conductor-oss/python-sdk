import logging
from unittest.mock import MagicMock

import pytest

from conductor.client.adapters.models.task_adapter import TaskAdapter
from conductor.client.adapters.models.workflow_adapter import WorkflowAdapter


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def mock_task():
    task = MagicMock(spec=TaskAdapter)
    task.status = "COMPLETED"
    task.task_def_name = "test_task"
    task.workflow_task = MagicMock()
    task.workflow_task.task_reference_name = "test_ref"
    return task


@pytest.fixture
def mock_task_in_progress():
    task = MagicMock(spec=TaskAdapter)
    task.status = "IN_PROGRESS"
    task.task_def_name = "in_progress_task"
    task.workflow_task = MagicMock()
    task.workflow_task.task_reference_name = "in_progress_ref"
    return task


@pytest.fixture
def mock_task_scheduled():
    task = MagicMock(spec=TaskAdapter)
    task.status = "SCHEDULED"
    task.task_def_name = "scheduled_task"
    task.workflow_task = MagicMock()
    task.workflow_task.task_reference_name = "scheduled_ref"
    return task


def test_is_completed_returns_true_for_completed_status():
    workflow = WorkflowAdapter()
    workflow.status = "COMPLETED"
    assert workflow.is_completed() is True


def test_is_completed_returns_true_for_failed_status():
    workflow = WorkflowAdapter()
    workflow.status = "FAILED"
    assert workflow.is_completed() is True


def test_is_completed_returns_true_for_terminated_status():
    workflow = WorkflowAdapter()
    workflow.status = "TERMINATED"
    assert workflow.is_completed() is True


def test_is_completed_returns_false_for_running_status():
    workflow = WorkflowAdapter()
    workflow.status = "RUNNING"
    assert workflow.is_completed() is False


def test_is_successful_returns_true_for_completed_status():
    workflow = WorkflowAdapter()
    workflow.status = "COMPLETED"
    assert workflow.is_successful() is True


def test_is_successful_returns_false_for_failed_status():
    workflow = WorkflowAdapter()
    workflow.status = "FAILED"
    assert workflow.is_successful() is False


def test_is_running_returns_true_for_running_status():
    workflow = WorkflowAdapter()
    workflow.status = "RUNNING"
    assert workflow.is_running() is True


def test_is_running_returns_true_for_paused_status():
    workflow = WorkflowAdapter()
    workflow.status = "PAUSED"
    assert workflow.is_running() is True


def test_is_running_returns_false_for_completed_status():
    workflow = WorkflowAdapter()
    workflow.status = "COMPLETED"
    assert workflow.is_running() is False


def test_is_failed_returns_true_for_failed_status():
    workflow = WorkflowAdapter()
    workflow.status = "FAILED"
    assert workflow.is_failed() is True


def test_is_failed_returns_true_for_timed_out_status():
    workflow = WorkflowAdapter()
    workflow.status = "TIMED_OUT"
    assert workflow.is_failed() is True


def test_is_failed_returns_true_for_terminated_status():
    workflow = WorkflowAdapter()
    workflow.status = "TERMINATED"
    assert workflow.is_failed() is True


def test_is_failed_returns_false_for_completed_status():
    workflow = WorkflowAdapter()
    workflow.status = "COMPLETED"
    assert workflow.is_failed() is False


def test_current_task_returns_none_when_no_tasks():
    workflow = WorkflowAdapter()
    workflow.tasks = None
    assert workflow.current_task is None


def test_current_task_returns_none_when_no_in_progress_tasks():
    workflow = WorkflowAdapter()
    workflow.tasks = [MagicMock(status="COMPLETED")]
    assert workflow.current_task is None


def test_current_task_returns_in_progress_task():
    workflow = WorkflowAdapter()
    in_progress_task = MagicMock(status="IN_PROGRESS")
    workflow.tasks = [MagicMock(status="COMPLETED"), in_progress_task]
    assert workflow.current_task == in_progress_task


def test_current_task_returns_scheduled_task():
    workflow = WorkflowAdapter()
    scheduled_task = MagicMock(status="SCHEDULED")
    workflow.tasks = [MagicMock(status="COMPLETED"), scheduled_task]
    assert workflow.current_task == scheduled_task


def test_get_in_progress_tasks_returns_empty_list_when_no_tasks():
    workflow = WorkflowAdapter()
    workflow.tasks = None
    assert workflow.get_in_progress_tasks() == []


def test_get_in_progress_tasks_returns_in_progress_tasks():
    workflow = WorkflowAdapter()
    in_progress_task = MagicMock(status="IN_PROGRESS")
    scheduled_task = MagicMock(status="SCHEDULED")
    completed_task = MagicMock(status="COMPLETED")
    workflow.tasks = [completed_task, in_progress_task, scheduled_task]
    result = workflow.get_in_progress_tasks()
    assert len(result) == 2
    assert in_progress_task in result
    assert scheduled_task in result


def test_get_task_by_reference_name_returns_none_when_no_tasks():
    workflow = WorkflowAdapter()
    workflow.tasks = None
    assert workflow.get_task_by_reference_name("test_ref") is None


def test_get_task_by_reference_name_returns_none_when_not_found():
    workflow = WorkflowAdapter()
    task = MagicMock()
    task.workflow_task = MagicMock()
    task.workflow_task.task_reference_name = "other_ref"
    workflow.tasks = [task]
    assert workflow.get_task_by_reference_name("test_ref") is None


def test_get_task_by_reference_name_returns_task_when_found():
    workflow = WorkflowAdapter()
    task = MagicMock()
    task.workflow_task = MagicMock()
    task.workflow_task.task_reference_name = "test_ref"
    workflow.tasks = [task]
    result = workflow.get_task_by_reference_name("test_ref")
    assert result == task


def test_get_task_by_reference_name_handles_missing_workflow_task():
    workflow = WorkflowAdapter()
    task = MagicMock()
    task.workflow_task = None
    workflow.tasks = [task]
    assert workflow.get_task_by_reference_name("test_ref") is None


def test_get_task_raises_error_when_no_parameters():
    workflow = WorkflowAdapter()
    with pytest.raises(
        ValueError, match="ONLY one of name or task_reference_name MUST be provided"
    ):
        workflow.get_task()


def test_get_task_raises_error_when_both_parameters():
    workflow = WorkflowAdapter()
    with pytest.raises(
        ValueError, match="ONLY one of name or task_reference_name MUST be provided"
    ):
        workflow.get_task(name="test", task_reference_name="test_ref")


def test_get_task_returns_none_when_no_tasks():
    workflow = WorkflowAdapter()
    workflow.tasks = None
    assert workflow.get_task(name="test") is None


def test_get_task_by_name_returns_task():
    workflow = WorkflowAdapter()
    task = MagicMock()
    task.task_def_name = "test_task"
    workflow.tasks = [task]
    result = workflow.get_task(name="test_task")
    assert result == task


def test_get_task_by_reference_name_legacy_returns_task():
    workflow = WorkflowAdapter()
    task = MagicMock()
    task.workflow_task = MagicMock()
    task.workflow_task.task_reference_name = "test_ref"
    workflow.tasks = [task]
    result = workflow.get_task(task_reference_name="test_ref")
    assert result == task
