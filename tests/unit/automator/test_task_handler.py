import multiprocessing

import pytest

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.automator.task_runner import TaskRunner
from conductor.client.configuration.configuration import Configuration
from tests.unit.resources.workers import ClassWorker


def test_initialization_with_invalid_workers(mocker):
    mocker.patch(
        "conductor.client.automator.task_handler._setup_logging_queue",
        return_value=(None, None),
    )
    with pytest.raises(Exception, match="Invalid worker"):
        TaskHandler(
            configuration=Configuration("http://localhost:8080/api"),
            workers=["invalid-worker"],
        )


def test_start_processes(mocker, valid_task_handler):
    mocker.patch.object(TaskRunner, "run", return_value=None)
    with valid_task_handler as task_handler:
        task_handler.start_processes()
        assert len(task_handler.task_runner_processes) == 1
        for process in task_handler.task_runner_processes:
            assert isinstance(process, multiprocessing.Process)


@pytest.fixture
def valid_task_handler():
    return TaskHandler(configuration=Configuration(), workers=[ClassWorker("task")])
