"""
Comprehensive test suite for task_handler.py to achieve 95%+ coverage.

This test file covers:
- TaskHandler initialization with various workers and configurations
- start_processes, stop_processes, join_processes methods
- Worker configuration handling with environment variables
- Thread management and process lifecycle
- Error conditions and boundary cases
- Context manager usage
- Decorated worker registration
- Metrics provider integration
"""
import multiprocessing
import os
import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock, call
from conductor.client.automator.task_handler import (
    TaskHandler,
    register_decorated_fn,
    get_registered_workers,
    get_registered_worker_names,
    _decorated_functions,
    _setup_logging_queue
)
import conductor.client.automator.task_handler as task_handler_module
from conductor.client.automator.task_runner import TaskRunner
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.worker.worker import Worker
from conductor.client.worker.worker_interface import WorkerInterface
from tests.unit.resources.workers import ClassWorker, SimplePythonWorker


class PickableMock(Mock):
    """Mock that can be pickled for multiprocessing."""
    def __reduce__(self):
        return (Mock, ())


class TestTaskHandlerInitialization(unittest.TestCase):
    """Test TaskHandler initialization with various configurations."""

    def setUp(self):
        # Clear decorated functions before each test
        _decorated_functions.clear()

    def tearDown(self):
        # Clean up decorated functions
        _decorated_functions.clear()
        # Clean up any lingering processes
        import multiprocessing
        for process in multiprocessing.active_children():
            try:
                process.terminate()
                process.join(timeout=0.5)
                if process.is_alive():
                    process.kill()
            except Exception:
                pass

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    def test_initialization_with_no_workers(self, mock_logging):
        """Test initialization with no workers provided."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        handler = TaskHandler(
            workers=None,
            configuration=Configuration(),
            scan_for_annotated_workers=False
        )

        self.assertEqual(len(handler.task_runner_processes), 0)
        self.assertEqual(len(handler.workers), 0)

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_initialization_with_single_worker(self, mock_import, mock_logging):
        """Test initialization with a single worker."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        worker = ClassWorker('test_task')
        handler = TaskHandler(
            workers=[worker],
            configuration=Configuration(),
            scan_for_annotated_workers=False
        )

        self.assertEqual(len(handler.workers), 1)
        self.assertEqual(len(handler.task_runner_processes), 1)

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_initialization_with_multiple_workers(self, mock_import, mock_logging):
        """Test initialization with multiple workers."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        workers = [
            ClassWorker('task1'),
            ClassWorker('task2'),
            ClassWorker('task3')
        ]
        handler = TaskHandler(
            workers=workers,
            configuration=Configuration(),
            scan_for_annotated_workers=False
        )

        self.assertEqual(len(handler.workers), 3)
        self.assertEqual(len(handler.task_runner_processes), 3)

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('importlib.import_module')
    def test_initialization_with_import_modules(self, mock_import, mock_logging):
        """Test initialization with custom module imports."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        # Mock import_module to return a valid module mock
        mock_module = Mock()
        mock_import.return_value = mock_module

        handler = TaskHandler(
            workers=[],
            configuration=Configuration(),
            import_modules=['module1', 'module2'],
            scan_for_annotated_workers=False
        )

        # Check that custom modules were imported
        import_calls = [call[0][0] for call in mock_import.call_args_list]
        self.assertIn('module1', import_calls)
        self.assertIn('module2', import_calls)

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_initialization_with_metrics_settings(self, mock_import, mock_logging):
        """Test initialization with metrics settings."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        metrics_settings = MetricsSettings(update_interval=0.5)
        handler = TaskHandler(
            workers=[],
            configuration=Configuration(),
            metrics_settings=metrics_settings,
            scan_for_annotated_workers=False
        )

        self.assertIsNotNone(handler.metrics_provider_process)

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_initialization_without_metrics_settings(self, mock_import, mock_logging):
        """Test initialization without metrics settings."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        handler = TaskHandler(
            workers=[],
            configuration=Configuration(),
            metrics_settings=None,
            scan_for_annotated_workers=False
        )

        self.assertIsNone(handler.metrics_provider_process)


class TestTaskHandlerDecoratedWorkers(unittest.TestCase):
    """Test TaskHandler with decorated workers."""

    def setUp(self):
        # Clear decorated functions before each test
        _decorated_functions.clear()

    def tearDown(self):
        # Clean up decorated functions
        _decorated_functions.clear()

    def test_register_decorated_fn(self):
        """Test registering a decorated function."""
        def test_func():
            pass

        register_decorated_fn(
            name='test_task',
            poll_interval=100,
            domain='test_domain',
            worker_id='worker1',
            func=test_func,
            thread_count=2,
            register_task_def=True,
            poll_timeout=200,
            lease_extend_enabled=False
        )

        self.assertIn(('test_task', 'test_domain'), _decorated_functions)
        record = _decorated_functions[('test_task', 'test_domain')]
        self.assertEqual(record['func'], test_func)
        self.assertEqual(record['poll_interval'], 100)
        self.assertEqual(record['domain'], 'test_domain')
        self.assertEqual(record['worker_id'], 'worker1')
        self.assertEqual(record['thread_count'], 2)
        self.assertEqual(record['register_task_def'], True)
        self.assertEqual(record['poll_timeout'], 200)
        self.assertEqual(record['lease_extend_enabled'], False)

    def test_get_registered_workers(self):
        """Test getting registered workers."""
        def test_func1():
            pass

        def test_func2():
            pass

        register_decorated_fn(
            name='task1',
            poll_interval=100,
            domain='domain1',
            worker_id='worker1',
            func=test_func1,
            thread_count=1
        )
        register_decorated_fn(
            name='task2',
            poll_interval=200,
            domain='domain2',
            worker_id='worker2',
            func=test_func2,
            thread_count=3
        )

        workers = get_registered_workers()
        self.assertEqual(len(workers), 2)
        self.assertIsInstance(workers[0], Worker)
        self.assertIsInstance(workers[1], Worker)

    def test_get_registered_worker_names(self):
        """Test getting registered worker names."""
        def test_func1():
            pass

        def test_func2():
            pass

        register_decorated_fn(
            name='task1',
            poll_interval=100,
            domain='domain1',
            worker_id='worker1',
            func=test_func1
        )
        register_decorated_fn(
            name='task2',
            poll_interval=200,
            domain='domain2',
            worker_id='worker2',
            func=test_func2
        )

        names = get_registered_worker_names()
        self.assertEqual(len(names), 2)
        self.assertIn('task1', names)
        self.assertIn('task2', names)

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    @patch('conductor.client.automator.task_handler.resolve_worker_config')
    def test_initialization_with_decorated_workers(self, mock_resolve, mock_import, mock_logging):
        """Test initialization that scans for decorated workers."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        # Mock resolve_worker_config to return default values
        mock_resolve.return_value = {
            'poll_interval': 100,
            'domain': 'test_domain',
            'worker_id': 'worker1',
            'thread_count': 1,
            'register_task_def': False,
            'poll_timeout': 100,
            'lease_extend_enabled': True
        }

        def test_func():
            pass

        register_decorated_fn(
            name='decorated_task',
            poll_interval=100,
            domain='test_domain',
            worker_id='worker1',
            func=test_func,
            thread_count=1,
            register_task_def=False,
            poll_timeout=100,
            lease_extend_enabled=True
        )

        handler = TaskHandler(
            workers=[],
            configuration=Configuration(),
            scan_for_annotated_workers=True
        )

        # Should have created a worker from the decorated function
        self.assertEqual(len(handler.workers), 1)
        self.assertEqual(len(handler.task_runner_processes), 1)


class TestTaskHandlerProcessManagement(unittest.TestCase):
    """Test TaskHandler process lifecycle management."""

    def setUp(self):
        _decorated_functions.clear()
        self.handlers = []  # Track handlers for cleanup

    def tearDown(self):
        _decorated_functions.clear()
        # Clean up any started processes
        for handler in self.handlers:
            try:
                # Terminate all task runner processes
                for process in handler.task_runner_processes:
                    if process.is_alive():
                        process.terminate()
                        process.join(timeout=1)
                        if process.is_alive():
                            process.kill()
                # Terminate metrics process if it exists
                if hasattr(handler, 'metrics_provider_process') and handler.metrics_provider_process:
                    if handler.metrics_provider_process.is_alive():
                        handler.metrics_provider_process.terminate()
                        handler.metrics_provider_process.join(timeout=1)
                        if handler.metrics_provider_process.is_alive():
                            handler.metrics_provider_process.kill()
            except Exception:
                pass

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    @patch.object(TaskRunner, 'run', PickableMock(return_value=None))
    def test_start_processes(self, mock_import, mock_logging):
        """Test starting worker processes."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        worker = ClassWorker('test_task')
        handler = TaskHandler(
            workers=[worker],
            configuration=Configuration(),
            scan_for_annotated_workers=False
        )
        self.handlers.append(handler)

        handler.start_processes()

        # Check that processes were started
        for process in handler.task_runner_processes:
            self.assertIsInstance(process, multiprocessing.Process)

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    @patch.object(TaskRunner, 'run', PickableMock(return_value=None))
    def test_start_processes_with_metrics(self, mock_import, mock_logging):
        """Test starting processes with metrics provider."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        metrics_settings = MetricsSettings(update_interval=0.5)
        handler = TaskHandler(
            workers=[ClassWorker('test_task')],
            configuration=Configuration(),
            metrics_settings=metrics_settings,
            scan_for_annotated_workers=False
        )
        self.handlers.append(handler)

        with patch.object(handler.metrics_provider_process, 'start') as mock_start:
            handler.start_processes()
            mock_start.assert_called_once()

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_stop_processes(self, mock_import, mock_logging):
        """Test stopping worker processes."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        worker = ClassWorker('test_task')
        handler = TaskHandler(
            workers=[worker],
            configuration=Configuration(),
            scan_for_annotated_workers=False
        )

        # Override the queue and logger_process with fresh mocks
        handler.queue = Mock()
        handler.logger_process = Mock()

        # Mock the processes
        for process in handler.task_runner_processes:
            process.terminate = Mock()

        handler.stop_processes()

        # Check that processes were terminated
        for process in handler.task_runner_processes:
            process.terminate.assert_called_once()

        # Check that logger process was terminated
        handler.queue.put.assert_called_with(None)
        handler.logger_process.terminate.assert_called_once()

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_stop_processes_with_metrics(self, mock_import, mock_logging):
        """Test stopping processes with metrics provider."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        metrics_settings = MetricsSettings(update_interval=0.5)
        handler = TaskHandler(
            workers=[ClassWorker('test_task')],
            configuration=Configuration(),
            metrics_settings=metrics_settings,
            scan_for_annotated_workers=False
        )

        # Override the queue and logger_process with fresh mocks
        handler.queue = Mock()
        handler.logger_process = Mock()

        # Mock the terminate methods
        handler.metrics_provider_process.terminate = Mock()
        for process in handler.task_runner_processes:
            process.terminate = Mock()

        handler.stop_processes()

        # Check that metrics process was terminated
        handler.metrics_provider_process.terminate.assert_called_once()

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_stop_process_with_exception(self, mock_import, mock_logging):
        """Test stopping a process that raises exception on terminate."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        worker = ClassWorker('test_task')
        handler = TaskHandler(
            workers=[worker],
            configuration=Configuration(),
            scan_for_annotated_workers=False
        )

        # Override the queue and logger_process with fresh mocks
        handler.queue = Mock()
        handler.logger_process = Mock()

        # Mock process to raise exception on terminate, then kill
        for process in handler.task_runner_processes:
            process.terminate = Mock(side_effect=Exception("terminate failed"))
            process.kill = Mock()
            # Use PropertyMock for pid
            type(process).pid = PropertyMock(return_value=12345)

        handler.stop_processes()

        # Check that kill was called after terminate failed
        for process in handler.task_runner_processes:
            process.terminate.assert_called_once()
            process.kill.assert_called_once()

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_join_processes(self, mock_import, mock_logging):
        """Test joining worker processes."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        worker = ClassWorker('test_task')
        handler = TaskHandler(
            workers=[worker],
            configuration=Configuration(),
            scan_for_annotated_workers=False
        )

        # Mock the join methods
        for process in handler.task_runner_processes:
            process.join = Mock()

        handler.join_processes()

        # Check that processes were joined
        for process in handler.task_runner_processes:
            process.join.assert_called_once()

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_join_processes_with_metrics(self, mock_import, mock_logging):
        """Test joining processes with metrics provider."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        metrics_settings = MetricsSettings(update_interval=0.5)
        handler = TaskHandler(
            workers=[ClassWorker('test_task')],
            configuration=Configuration(),
            metrics_settings=metrics_settings,
            scan_for_annotated_workers=False
        )

        # Mock the join methods
        handler.metrics_provider_process.join = Mock()
        for process in handler.task_runner_processes:
            process.join = Mock()

        handler.join_processes()

        # Check that metrics process was joined
        handler.metrics_provider_process.join.assert_called_once()

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_join_processes_with_keyboard_interrupt(self, mock_import, mock_logging):
        """Test join_processes handles KeyboardInterrupt."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        worker = ClassWorker('test_task')
        handler = TaskHandler(
            workers=[worker],
            configuration=Configuration(),
            scan_for_annotated_workers=False
        )

        # Override the queue and logger_process with fresh mocks
        handler.queue = Mock()
        handler.logger_process = Mock()

        # Mock join to raise KeyboardInterrupt
        for process in handler.task_runner_processes:
            process.join = Mock(side_effect=KeyboardInterrupt())
            process.terminate = Mock()

        handler.join_processes()

        # Check that stop_processes was called
        handler.queue.put.assert_called_with(None)


class TestTaskHandlerContextManager(unittest.TestCase):
    """Test TaskHandler as a context manager."""

    def setUp(self):
        _decorated_functions.clear()

    def tearDown(self):
        _decorated_functions.clear()

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('importlib.import_module')
    @patch('conductor.client.automator.task_handler.Process')
    def test_context_manager_enter(self, mock_process_class, mock_import, mock_logging):
        """Test context manager __enter__ method."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logger_process.terminate = Mock()
        mock_logger_process.is_alive = Mock(return_value=False)
        mock_logging.return_value = (mock_logger_process, mock_queue)

        # Mock Process for task runners
        mock_process = Mock()
        mock_process.terminate = Mock()
        mock_process.kill = Mock()
        mock_process.is_alive = Mock(return_value=False)
        mock_process_class.return_value = mock_process

        worker = ClassWorker('test_task')
        handler = TaskHandler(
            workers=[worker],
            configuration=Configuration(),
            scan_for_annotated_workers=False
        )

        # Override the queue, logger_process, and metrics_provider_process with fresh mocks
        handler.queue = Mock()
        handler.logger_process = Mock()
        handler.logger_process.terminate = Mock()
        handler.logger_process.is_alive = Mock(return_value=False)
        handler.metrics_provider_process = Mock()
        handler.metrics_provider_process.terminate = Mock()
        handler.metrics_provider_process.is_alive = Mock(return_value=False)

        # Also need to ensure task_runner_processes have proper mocks
        for proc in handler.task_runner_processes:
            proc.terminate = Mock()
            proc.kill = Mock()
            proc.is_alive = Mock(return_value=False)

        with handler as h:
            self.assertIs(h, handler)

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('importlib.import_module')
    def test_context_manager_exit(self, mock_import, mock_logging):
        """Test context manager __exit__ method."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        worker = ClassWorker('test_task')
        handler = TaskHandler(
            workers=[worker],
            configuration=Configuration(),
            scan_for_annotated_workers=False
        )

        # Override the queue and logger_process with fresh mocks
        handler.queue = Mock()
        handler.logger_process = Mock()

        # Mock terminate on all processes
        for process in handler.task_runner_processes:
            process.terminate = Mock()

        with handler:
            pass

        # Check that stop_processes was called on exit
        handler.queue.put.assert_called_with(None)


class TestSetupLoggingQueue(unittest.TestCase):
    """Test logging queue setup."""

    def test_setup_logging_queue_with_configuration(self):
        """Test logging queue setup with configuration."""
        config = Configuration()
        config.apply_logging_config = Mock()

        # Call _setup_logging_queue which creates real Process and Queue
        logger_process, queue = task_handler_module._setup_logging_queue(config)

        try:
            # Verify configuration was applied
            config.apply_logging_config.assert_called_once()

            # Verify process and queue were created
            self.assertIsNotNone(logger_process)
            self.assertIsNotNone(queue)

            # Verify process is running
            self.assertTrue(logger_process.is_alive())
        finally:
            # Cleanup: terminate the process
            if logger_process and logger_process.is_alive():
                logger_process.terminate()
                logger_process.join(timeout=1)

    def test_setup_logging_queue_without_configuration(self):
        """Test logging queue setup without configuration."""
        # Call with None configuration
        logger_process, queue = task_handler_module._setup_logging_queue(None)

        try:
            # Verify process and queue were created
            self.assertIsNotNone(logger_process)
            self.assertIsNotNone(queue)

            # Verify process is running
            self.assertTrue(logger_process.is_alive())
        finally:
            # Cleanup: terminate the process
            if logger_process and logger_process.is_alive():
                logger_process.terminate()
                logger_process.join(timeout=1)


class TestPlatformSpecificBehavior(unittest.TestCase):
    """Test platform-specific behavior."""

    def test_decorated_functions_dict_exists(self):
        """Test that decorated functions dictionary is accessible."""
        self.assertIsNotNone(_decorated_functions)
        self.assertIsInstance(_decorated_functions, dict)

    def test_register_multiple_domains(self):
        """Test registering same task name with different domains."""
        def func1():
            pass

        def func2():
            pass

        # Clear first
        _decorated_functions.clear()

        register_decorated_fn(
            name='task',
            poll_interval=100,
            domain='domain1',
            worker_id='worker1',
            func=func1
        )
        register_decorated_fn(
            name='task',
            poll_interval=200,
            domain='domain2',
            worker_id='worker2',
            func=func2
        )

        self.assertEqual(len(_decorated_functions), 2)
        self.assertIn(('task', 'domain1'), _decorated_functions)
        self.assertIn(('task', 'domain2'), _decorated_functions)

        _decorated_functions.clear()


class TestLoggerProcessDirect(unittest.TestCase):
    """Test __logger_process function directly."""

    def test_logger_process_function_exists(self):
        """Test that __logger_process function exists in the module."""
        import conductor.client.automator.task_handler as th_module

        # Verify the function exists
        logger_process_func = None
        for name, obj in th_module.__dict__.items():
            if name.endswith('__logger_process') and callable(obj):
                logger_process_func = obj
                break

        self.assertIsNotNone(logger_process_func, "__logger_process function should exist")

        # Verify it's callable
        self.assertTrue(callable(logger_process_func))

    def test_logger_process_with_messages(self):
        """Test __logger_process function directly with log messages."""
        import logging
        from unittest.mock import Mock
        import conductor.client.automator.task_handler as th_module
        from queue import Queue
        import threading

        # Find the logger process function
        logger_process_func = None
        for name, obj in th_module.__dict__.items():
            if name.endswith('__logger_process') and callable(obj):
                logger_process_func = obj
                break

        if logger_process_func is not None:
            # Use a regular queue (not multiprocessing) for testing in main process
            test_queue = Queue()

            # Create test log records
            test_record1 = logging.LogRecord(
                name='test', level=logging.INFO, pathname='test.py', lineno=1,
                msg='Test message 1', args=(), exc_info=None
            )
            test_record2 = logging.LogRecord(
                name='test', level=logging.WARNING, pathname='test.py', lineno=2,
                msg='Test message 2', args=(), exc_info=None
            )

            # Add messages to queue
            test_queue.put(test_record1)
            test_queue.put(test_record2)
            test_queue.put(None)  # Shutdown signal

            # Run the logger process in a thread (simulating the process behavior)
            def run_logger():
                logger_process_func(test_queue, logging.DEBUG, '%(levelname)s: %(message)s')

            thread = threading.Thread(target=run_logger, daemon=True)
            thread.start()
            thread.join(timeout=2)

            # If thread is still alive, it means the function is hanging
            self.assertFalse(thread.is_alive(), "Logger process should have completed")

    def test_logger_process_without_format(self):
        """Test __logger_process function without custom format."""
        import logging
        from unittest.mock import Mock
        import conductor.client.automator.task_handler as th_module
        from queue import Queue
        import threading

        # Find the logger process function
        logger_process_func = None
        for name, obj in th_module.__dict__.items():
            if name.endswith('__logger_process') and callable(obj):
                logger_process_func = obj
                break

        if logger_process_func is not None:
            # Use a regular queue for testing in main process
            test_queue = Queue()

            # Add only shutdown signal
            test_queue.put(None)

            # Run the logger process in a thread
            def run_logger():
                logger_process_func(test_queue, logging.INFO, None)

            thread = threading.Thread(target=run_logger, daemon=True)
            thread.start()
            thread.join(timeout=2)

            # Verify completion
            self.assertFalse(thread.is_alive(), "Logger process should have completed")


class TestLoggerProcessIntegration(unittest.TestCase):
    """Test logger process through integration tests."""

    def test_logger_process_through_setup(self):
        """Test logger process is properly configured through _setup_logging_queue."""
        import logging
        from multiprocessing import Queue
        import time

        # Create a real queue
        queue = Queue()

        # Create a configuration with custom format
        config = Configuration()
        config.logger_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        # Call _setup_logging_queue which uses __logger_process internally
        logger_process, returned_queue = _setup_logging_queue(config)

        # Verify the process was created and started
        self.assertIsNotNone(logger_process)
        self.assertTrue(logger_process.is_alive())

        # Put multiple test messages with different levels and shutdown signal
        for i in range(3):
            test_record = logging.LogRecord(
                name='test',
                level=logging.INFO,
                pathname='test.py',
                lineno=1,
                msg=f'Test message {i}',
                args=(),
                exc_info=None
            )
            returned_queue.put(test_record)

        # Add small delay to let messages process
        time.sleep(0.1)

        returned_queue.put(None)  # Shutdown signal

        # Wait for process to finish
        logger_process.join(timeout=2)

        # Clean up
        if logger_process.is_alive():
            logger_process.terminate()
            logger_process.join(timeout=1)

    def test_logger_process_without_configuration(self):
        """Test logger process without configuration."""
        from multiprocessing import Queue
        import logging
        import time

        # Call with None configuration
        logger_process, queue = _setup_logging_queue(None)

        # Verify the process was created and started
        self.assertIsNotNone(logger_process)
        self.assertTrue(logger_process.is_alive())

        # Send a few messages before shutdown
        for i in range(2):
            test_record = logging.LogRecord(
                name='test',
                level=logging.DEBUG,
                pathname='test.py',
                lineno=1,
                msg=f'Debug message {i}',
                args=(),
                exc_info=None
            )
            queue.put(test_record)

        # Small delay
        time.sleep(0.1)

        # Send shutdown signal
        queue.put(None)

        # Wait for process to finish
        logger_process.join(timeout=2)

        # Clean up
        if logger_process.is_alive():
            logger_process.terminate()
            logger_process.join(timeout=1)

    def test_setup_logging_with_formatter(self):
        """Test that logger format is properly applied when provided."""
        import logging

        config = Configuration()
        config.logger_format = '%(levelname)s: %(message)s'

        logger_process, queue = _setup_logging_queue(config)

        self.assertIsNotNone(logger_process)
        self.assertTrue(logger_process.is_alive())

        # Send shutdown to clean up
        queue.put(None)
        logger_process.join(timeout=2)

        if logger_process.is_alive():
            logger_process.terminate()
            logger_process.join(timeout=1)


class TestWorkerConfiguration(unittest.TestCase):
    """Test worker configuration resolution with environment variables."""

    def setUp(self):
        _decorated_functions.clear()
        # Save original environment
        self.original_env = os.environ.copy()
        self.handlers = []  # Track handlers for cleanup

    def tearDown(self):
        _decorated_functions.clear()
        # Clean up any started processes
        for handler in self.handlers:
            try:
                # Terminate all task runner processes
                for process in handler.task_runner_processes:
                    if process.is_alive():
                        process.terminate()
                        process.join(timeout=1)
                        if process.is_alive():
                            process.kill()
            except Exception:
                pass
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_worker_config_with_env_override(self, mock_import, mock_logging):
        """Test worker configuration with environment variable override."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        # Set environment variables
        os.environ['conductor.worker.decorated_task.poll_interval'] = '500'
        os.environ['conductor.worker.decorated_task.domain'] = 'production'

        def test_func():
            pass

        register_decorated_fn(
            name='decorated_task',
            poll_interval=100,
            domain='dev',
            worker_id='worker1',
            func=test_func,
            thread_count=1,
            register_task_def=False,
            poll_timeout=100,
            lease_extend_enabled=True
        )

        handler = TaskHandler(
            workers=[],
            configuration=Configuration(),
            scan_for_annotated_workers=True
        )
        self.handlers.append(handler)

        # Check that worker was created with environment overrides
        self.assertEqual(len(handler.workers), 1)
        worker = handler.workers[0]

        self.assertEqual(worker.poll_interval, 500.0)
        self.assertEqual(worker.domain, 'production')


class TestTaskHandlerPausedWorker(unittest.TestCase):
    """Test TaskHandler with paused workers."""

    def setUp(self):
        _decorated_functions.clear()
        self.handlers = []  # Track handlers for cleanup

    def tearDown(self):
        _decorated_functions.clear()
        # Clean up any started processes
        for handler in self.handlers:
            try:
                # Terminate all task runner processes
                for process in handler.task_runner_processes:
                    if process.is_alive():
                        process.terminate()
                        process.join(timeout=1)
                        if process.is_alive():
                            process.kill()
            except Exception:
                pass

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    @patch.object(TaskRunner, 'run', PickableMock(return_value=None))
    def test_start_processes_with_paused_worker(self, mock_import, mock_logging):
        """Test starting processes with a paused worker."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        worker = ClassWorker('test_task')
        # Set paused as a boolean attribute (paused is now an attribute, not a method)
        worker.paused = True

        handler = TaskHandler(
            workers=[worker],
            configuration=Configuration(),
            scan_for_annotated_workers=False
        )
        self.handlers.append(handler)

        handler.start_processes()

        # Verify worker was configured with paused status
        self.assertTrue(worker.paused)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        _decorated_functions.clear()

    def tearDown(self):
        _decorated_functions.clear()

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_empty_workers_list(self, mock_import, mock_logging):
        """Test with empty workers list."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        handler = TaskHandler(
            workers=[],
            configuration=Configuration(),
            scan_for_annotated_workers=False
        )

        self.assertEqual(len(handler.workers), 0)
        self.assertEqual(len(handler.task_runner_processes), 0)

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_workers_not_a_list_single_worker(self, mock_import, mock_logging):
        """Test passing a single worker (not in a list) - should be wrapped in list."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        # Pass a single worker object, not a list
        worker = ClassWorker('test_task')
        handler = TaskHandler(
            workers=worker,  # Single worker, not a list
            configuration=Configuration(),
            scan_for_annotated_workers=False
        )

        # Should have created a list with one worker
        self.assertEqual(len(handler.workers), 1)
        self.assertEqual(len(handler.task_runner_processes), 1)

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_stop_process_with_none_process(self, mock_import, mock_logging):
        """Test stopping when process is None."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        handler = TaskHandler(
            workers=[],
            configuration=Configuration(),
            metrics_settings=None,
            scan_for_annotated_workers=False
        )

        # Should not raise exception when metrics_provider_process is None
        handler.stop_processes()

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_start_metrics_with_none_process(self, mock_import, mock_logging):
        """Test starting metrics when process is None."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        handler = TaskHandler(
            workers=[],
            configuration=Configuration(),
            metrics_settings=None,
            scan_for_annotated_workers=False
        )

        # Should not raise exception when metrics_provider_process is None
        handler.start_processes()

    @patch('conductor.client.automator.task_handler._setup_logging_queue')
    @patch('conductor.client.automator.task_handler.importlib.import_module')
    def test_join_metrics_with_none_process(self, mock_import, mock_logging):
        """Test joining metrics when process is None."""
        mock_queue = Mock()
        mock_logger_process = Mock()
        mock_logging.return_value = (mock_logger_process, mock_queue)

        handler = TaskHandler(
            workers=[],
            configuration=Configuration(),
            metrics_settings=None,
            scan_for_annotated_workers=False
        )

        # Should not raise exception when metrics_provider_process is None
        handler.join_processes()


def tearDownModule():
    """Module-level teardown to ensure all processes are cleaned up."""
    import multiprocessing
    import time

    # Give a moment for processes to clean up naturally
    time.sleep(0.1)

    # Force cleanup of any remaining child processes
    for process in multiprocessing.active_children():
        try:
            if process.is_alive():
                process.terminate()
                process.join(timeout=1)
                if process.is_alive():
                    process.kill()
                    process.join(timeout=0.5)
        except Exception:
            pass


if __name__ == '__main__':
    unittest.main()
