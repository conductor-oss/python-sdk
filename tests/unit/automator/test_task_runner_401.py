import pytest
from unittest.mock import Mock, patch, MagicMock

from conductor.client.automator.task_runner import TaskRunner
from conductor.client.configuration.configuration import Configuration
from conductor.client.worker.worker_interface import WorkerInterface
from conductor.client.codegen.rest import AuthorizationException


class MockWorker(WorkerInterface):
    def __init__(self):
        super().__init__("test_task")
        self._paused = False
    
    def execute(self, task):
        return Mock()
    
    def paused(self):
        return self._paused
    
    def get_domain(self):
        return "test_domain"
    
    def get_identity(self):
        return "test_worker"


class TestTaskRunner401Policy:
    def test_task_runner_uses_api_client(self):
        config = Configuration()
        worker = MockWorker()
        
        with patch('conductor.client.automator.task_runner.TaskResourceApi') as mock_task_api:
            with patch('conductor.client.automator.task_runner.ApiClient') as mock_api_client:
                task_runner = TaskRunner(worker, config)
                
                # Should use ApiClient
                mock_api_client.assert_called_once_with(configuration=config)
                mock_task_api.assert_called_once()

    def test_task_runner_checks_401_stop_condition(self):
        config = Configuration(auth_401_max_attempts=1)
        worker = MockWorker()
        
        with patch('conductor.client.automator.task_runner.TaskResourceApi') as mock_task_api:
            with patch('conductor.client.automator.task_runner.ApiClient') as mock_api_client:
                # Mock the ApiClient with 401 handler
                mock_api_client_instance = Mock()
                mock_api_client_instance.auth_401_handler = Mock()
                mock_api_client_instance.auth_401_handler.is_worker_stopped.return_value = True
                mock_api_client.return_value = mock_api_client_instance
                
                # Mock TaskResourceApi to expose the api_client
                mock_task_api_instance = Mock()
                mock_task_api_instance.api_client = mock_api_client_instance
                mock_task_api.return_value = mock_task_api_instance
                
                task_runner = TaskRunner(worker, config)
                
                # Mock the run_once method to prevent infinite loop
                task_runner.run_once = Mock()
                
                # Should break out of loop when worker is stopped
                task_runner.run()
                
                # Should check stop condition
                mock_api_client_instance.auth_401_handler.is_worker_stopped.assert_called()

    def test_task_runner_continues_when_not_stopped(self):
        config = Configuration()
        worker = MockWorker()
        
        with patch('conductor.client.automator.task_runner.TaskResourceApi') as mock_task_api:
            with patch('conductor.client.automator.task_runner.ApiClient') as mock_api_client:
                # Mock the ApiClient with 401 handler
                mock_api_client_instance = Mock()
                mock_api_client_instance.auth_401_handler = Mock()
                # Return False first, then raise exception to break loop
                mock_api_client_instance.auth_401_handler.is_worker_stopped.side_effect = [False, KeyboardInterrupt]
                mock_api_client.return_value = mock_api_client_instance
                
                # Mock TaskResourceApi to expose the api_client
                mock_task_api_instance = Mock()
                mock_task_api_instance.api_client = mock_api_client_instance
                mock_task_api.return_value = mock_task_api_instance
                
                task_runner = TaskRunner(worker, config)
                
                # Mock the run_once method to prevent infinite loop
                task_runner.run_once = Mock()
                
                # Should continue running when not stopped (until KeyboardInterrupt)
                try:
                    task_runner.run()
                except KeyboardInterrupt:
                    pass
                
                # Should check stop condition
                mock_api_client_instance.auth_401_handler.is_worker_stopped.assert_called()

    def test_task_runner_handles_missing_auth_handler(self):
        config = Configuration()
        worker = MockWorker()
        
        with patch('conductor.client.automator.task_runner.TaskResourceApi') as mock_task_api:
            with patch('conductor.client.automator.task_runner.ApiClient') as mock_api_client:
                # Mock the ApiClient without auth_401_handler
                mock_api_client_instance = Mock()
                del mock_api_client_instance.auth_401_handler
                mock_api_client.return_value = mock_api_client_instance
                
                # Mock TaskResourceApi to expose the api_client
                mock_task_api_instance = Mock()
                mock_task_api_instance.api_client = mock_api_client_instance
                mock_task_api.return_value = mock_task_api_instance
                
                task_runner = TaskRunner(worker, config)
                
                # Mock the run_once method to raise exception after first call
                task_runner.run_once = Mock(side_effect=KeyboardInterrupt)
                
                # Should not crash when auth_401_handler is missing
                try:
                    task_runner.run()
                except KeyboardInterrupt:
                    pass

    @patch('conductor.client.automator.task_runner.logger')
    def test_task_runner_logs_worker_stop(self, mock_logger):
        config = Configuration(auth_401_max_attempts=1)
        worker = MockWorker()
        
        with patch('conductor.client.automator.task_runner.TaskResourceApi') as mock_task_api:
            with patch('conductor.client.automator.task_runner.ApiClient') as mock_api_client:
                # Mock the ApiClient with 401 handler
                mock_api_client_instance = Mock()
                mock_api_client_instance.auth_401_handler = Mock()
                mock_api_client_instance.auth_401_handler.is_worker_stopped.return_value = True
                mock_api_client.return_value = mock_api_client_instance
                
                # Mock TaskResourceApi to expose the api_client
                mock_task_api_instance = Mock()
                mock_task_api_instance.api_client = mock_api_client_instance
                mock_task_api.return_value = mock_task_api_instance
                
                task_runner = TaskRunner(worker, config)
                
                task_runner.run_once = Mock()

                task_runner.run()
                
                mock_logger.error.assert_called_with(
                    "Worker stopped due to persistent 401 authentication failures"
                )

    def test_task_runner_401_policy_integration(self):
        config = Configuration(auth_401_max_attempts=2)
        worker = MockWorker()
        
        with patch('conductor.client.automator.task_runner.TaskResourceApi') as mock_task_api:
            with patch('conductor.client.automator.task_runner.ApiClient') as mock_api_client:
                # Mock the ApiClient with 401 handler
                mock_api_client_instance = Mock()
                mock_api_client_instance.auth_401_handler = Mock()
                mock_api_client_instance.auth_401_handler.is_worker_stopped.side_effect = [False, KeyboardInterrupt]
                mock_api_client.return_value = mock_api_client_instance
                
                # Mock TaskResourceApi to expose the api_client
                mock_task_api_instance = Mock()
                mock_task_api_instance.api_client = mock_api_client_instance
                mock_task_api.return_value = mock_task_api_instance
                
                task_runner = TaskRunner(worker, config)
                task_runner.run_once = Mock()
                
                try:
                    task_runner.run()
                except KeyboardInterrupt:
                    pass
                
                mock_api_client.assert_called_once_with(configuration=config)
