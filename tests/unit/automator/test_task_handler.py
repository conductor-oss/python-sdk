import multiprocessing
import tempfile
import unittest
from unittest.mock import Mock
from unittest.mock import patch

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.automator.task_runner import TaskRunner
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from tests.unit.resources.workers import ClassWorker


class PickableMock(Mock):
    def __reduce__(self):
        return (Mock, ())


class TestTaskHandler(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_initialization_with_invalid_workers(self):
        expected_exception = Exception('Invalid worker list')
        with self.assertRaises(Exception) as context:
            TaskHandler(
                configuration=Configuration(),
                workers=ClassWorker()
            )
            self.assertEqual(expected_exception, context.exception)

    def test_start_processes(self):
        with patch.object(TaskRunner, 'run', PickableMock(return_value=None)):
            task_handler = _get_valid_task_handler()
            with task_handler:
                task_handler.start_processes()
                self.assertEqual(len(task_handler.task_runner_processes), 1)
                for process in task_handler.task_runner_processes:
                    self.assertTrue(
                        isinstance(process, multiprocessing.Process)
                    )

    def test_metrics_directory_cleaned_once_in_parent_init(self):
        """TaskHandler.__init__ (parent, pre-spawn) invokes
        clean_metrics_directory exactly once. Spawned workers rely on the
        non-destructive create_metrics_collector path and never clean, so this
        parent-owned call is the single point where .db files are wiped."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            metrics_settings = MetricsSettings(directory=tmp_dir, clean_directory=True)
            metrics_settings.clean_metrics_directory = Mock()

            task_handler = TaskHandler(
                configuration=Configuration(),
                workers=[ClassWorker('task')],
                metrics_settings=metrics_settings,
            )
            with task_handler:
                metrics_settings.clean_metrics_directory.assert_called_once_with()


def _get_valid_task_handler():
    return TaskHandler(
        configuration=Configuration(),
        workers=[
            ClassWorker('task')
        ]
    )
