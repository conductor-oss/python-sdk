"""
Unit tests for multi-homed workers functionality.

Tests cover:
1. Configuration.from_env_multi() - comma-separated env var parsing
2. Thread-safe task_server_map operations
3. TaskRunner/AsyncTaskRunner multi-config initialization
4. Credential validation
5. Backward compatibility
"""

import os
import pytest
import threading
import time
from unittest.mock import patch, MagicMock

from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings


class TestConfigurationFromEnvMulti:
    """Tests for Configuration.from_env_multi() factory method."""
    
    def test_no_env_vars_returns_default(self):
        """When no env vars set, returns list with default configuration."""
        with patch.dict(os.environ, {}, clear=True):
            # Clear any existing conductor env vars
            for key in ['CONDUCTOR_SERVER_URL', 'CONDUCTOR_AUTH_KEY', 'CONDUCTOR_AUTH_SECRET']:
                os.environ.pop(key, None)
            
            configs = Configuration.from_env_multi()
            
            assert len(configs) == 1
            assert isinstance(configs[0], Configuration)
    
    def test_single_server_no_auth(self):
        """Single server URL without auth credentials."""
        with patch.dict(os.environ, {
            'CONDUCTOR_SERVER_URL': 'https://server1.example.com/api'
        }, clear=True):
            configs = Configuration.from_env_multi()
            
            assert len(configs) == 1
            assert configs[0].host == 'https://server1.example.com/api'
            assert configs[0].authentication_settings is None
    
    def test_single_server_with_auth(self):
        """Single server with auth credentials."""
        with patch.dict(os.environ, {
            'CONDUCTOR_SERVER_URL': 'https://server1.example.com/api',
            'CONDUCTOR_AUTH_KEY': 'key1',
            'CONDUCTOR_AUTH_SECRET': 'secret1'
        }, clear=True):
            configs = Configuration.from_env_multi()
            
            assert len(configs) == 1
            assert configs[0].host == 'https://server1.example.com/api'
            assert configs[0].authentication_settings is not None
            assert configs[0].authentication_settings.key_id == 'key1'
            assert configs[0].authentication_settings.key_secret == 'secret1'
    
    def test_multiple_servers_no_auth(self):
        """Multiple servers without auth credentials."""
        with patch.dict(os.environ, {
            'CONDUCTOR_SERVER_URL': 'https://east.example.com/api,https://west.example.com/api'
        }, clear=True):
            configs = Configuration.from_env_multi()
            
            assert len(configs) == 2
            assert configs[0].host == 'https://east.example.com/api'
            assert configs[1].host == 'https://west.example.com/api'
            assert configs[0].authentication_settings is None
            assert configs[1].authentication_settings is None
    
    def test_multiple_servers_with_auth(self):
        """Multiple servers with matching auth credentials."""
        with patch.dict(os.environ, {
            'CONDUCTOR_SERVER_URL': 'https://east.example.com/api,https://west.example.com/api',
            'CONDUCTOR_AUTH_KEY': 'key1,key2',
            'CONDUCTOR_AUTH_SECRET': 'secret1,secret2'
        }, clear=True):
            configs = Configuration.from_env_multi()
            
            assert len(configs) == 2
            assert configs[0].host == 'https://east.example.com/api'
            assert configs[0].authentication_settings.key_id == 'key1'
            assert configs[0].authentication_settings.key_secret == 'secret1'
            assert configs[1].host == 'https://west.example.com/api'
            assert configs[1].authentication_settings.key_id == 'key2'
            assert configs[1].authentication_settings.key_secret == 'secret2'
    
    def test_whitespace_handling(self):
        """Whitespace around values is trimmed."""
        with patch.dict(os.environ, {
            'CONDUCTOR_SERVER_URL': '  https://east.example.com/api , https://west.example.com/api  ',
            'CONDUCTOR_AUTH_KEY': '  key1 , key2  ',
            'CONDUCTOR_AUTH_SECRET': '  secret1 , secret2  '
        }, clear=True):
            configs = Configuration.from_env_multi()
            
            assert len(configs) == 2
            assert configs[0].host == 'https://east.example.com/api'
            assert configs[1].host == 'https://west.example.com/api'
            assert configs[0].authentication_settings.key_id == 'key1'
            assert configs[1].authentication_settings.key_id == 'key2'
    
    def test_mismatched_key_count_raises(self):
        """Mismatched key count raises ValueError."""
        with patch.dict(os.environ, {
            'CONDUCTOR_SERVER_URL': 'https://east.example.com/api,https://west.example.com/api',
            'CONDUCTOR_AUTH_KEY': 'key1',  # Only one key for two servers
            'CONDUCTOR_AUTH_SECRET': 'secret1,secret2'
        }, clear=True):
            with pytest.raises(ValueError) as exc_info:
                Configuration.from_env_multi()
            
            assert "CONDUCTOR_AUTH_KEY count (1)" in str(exc_info.value)
            assert "CONDUCTOR_SERVER_URL count (2)" in str(exc_info.value)
    
    def test_mismatched_secret_count_raises(self):
        """Mismatched secret count raises ValueError."""
        with patch.dict(os.environ, {
            'CONDUCTOR_SERVER_URL': 'https://east.example.com/api,https://west.example.com/api',
            'CONDUCTOR_AUTH_KEY': 'key1,key2',
            'CONDUCTOR_AUTH_SECRET': 'secret1'  # Only one secret for two servers
        }, clear=True):
            with pytest.raises(ValueError) as exc_info:
                Configuration.from_env_multi()
            
            assert "CONDUCTOR_AUTH_SECRET count (1)" in str(exc_info.value)
    
    def test_key_without_secret_raises(self):
        """Key without secret raises ValueError."""
        with patch.dict(os.environ, {
            'CONDUCTOR_SERVER_URL': 'https://server1.example.com/api',
            'CONDUCTOR_AUTH_KEY': 'key1'
            # No CONDUCTOR_AUTH_SECRET
        }, clear=True):
            with pytest.raises(ValueError) as exc_info:
                Configuration.from_env_multi()
            
            assert "must be provided together" in str(exc_info.value)
    
    def test_secret_without_key_raises(self):
        """Secret without key raises ValueError."""
        with patch.dict(os.environ, {
            'CONDUCTOR_SERVER_URL': 'https://server1.example.com/api',
            'CONDUCTOR_AUTH_SECRET': 'secret1'
            # No CONDUCTOR_AUTH_KEY
        }, clear=True):
            with pytest.raises(ValueError) as exc_info:
                Configuration.from_env_multi()
            
            assert "must be provided together" in str(exc_info.value)
    
    def test_empty_values_filtered(self):
        """Empty values in comma-separated list are filtered out."""
        with patch.dict(os.environ, {
            'CONDUCTOR_SERVER_URL': 'https://server1.example.com/api,,https://server2.example.com/api,'
        }, clear=True):
            configs = Configuration.from_env_multi()
            
            assert len(configs) == 2
            assert configs[0].host == 'https://server1.example.com/api'
            assert configs[1].host == 'https://server2.example.com/api'


class TestTaskServerMapThreadSafety:
    """Tests for thread-safe task_server_map operations."""
    
    def test_concurrent_writes_and_reads(self):
        """Simulate concurrent map access from multiple threads."""
        from conductor.client.automator.task_runner import TaskRunner
        from conductor.client.worker.worker_interface import WorkerInterface
        
        # Create a mock worker
        worker = MagicMock(spec=WorkerInterface)
        worker.get_task_definition_name.return_value = 'test_task'
        worker.task_definition_names = ['test_task']
        worker.thread_count = 4
        worker.poll_interval = 1
        worker.domain = None
        worker.worker_id = 'test-worker'
        worker.register_task_def = False
        worker.poll_timeout = 100
        worker.lease_extend_enabled = False
        worker.paused = False
        worker.overwrite_task_def = True
        worker.strict_schema = False
        
        config = Configuration(server_api_url='http://localhost:8080/api')
        runner = TaskRunner(worker, configuration=config)
        
        # Verify lock exists
        assert hasattr(runner, '_task_server_map_lock')
        assert isinstance(runner._task_server_map_lock, type(threading.Lock()))
        
        errors = []
        
        def writer_thread(thread_id):
            """Simulate poll thread writing to map."""
            try:
                for i in range(100):
                    task_id = f"task-{thread_id}-{i}"
                    with runner._task_server_map_lock:
                        runner._task_server_map[task_id] = thread_id % 2
                    time.sleep(0.0001)
            except Exception as e:
                errors.append(e)
        
        def reader_thread(thread_id):
            """Simulate update thread reading from map."""
            try:
                for i in range(100):
                    task_id = f"task-{thread_id}-{i}"
                    with runner._task_server_map_lock:
                        runner._task_server_map.pop(task_id, 0)
                    time.sleep(0.0001)
            except Exception as e:
                errors.append(e)
        
        # Start threads
        threads = []
        for i in range(4):
            t1 = threading.Thread(target=writer_thread, args=(i,))
            t2 = threading.Thread(target=reader_thread, args=(i,))
            threads.extend([t1, t2])
            t1.start()
            t2.start()
        
        # Wait for completion
        for t in threads:
            t.join(timeout=5)
        
        # No errors should have occurred
        assert len(errors) == 0, f"Thread errors: {errors}"


class TestMultiHomedRunnerInitialization:
    """Tests for TaskRunner and AsyncTaskRunner multi-config initialization."""
    
    def test_task_runner_single_config(self):
        """TaskRunner with single configuration (backward compatible)."""
        from conductor.client.automator.task_runner import TaskRunner
        from conductor.client.worker.worker_interface import WorkerInterface
        
        worker = MagicMock(spec=WorkerInterface)
        worker.get_task_definition_name.return_value = 'test_task'
        worker.task_definition_names = ['test_task']
        worker.thread_count = 1
        worker.poll_interval = 1
        worker.domain = None
        worker.worker_id = 'test-worker'
        worker.register_task_def = False
        worker.poll_timeout = 100
        worker.lease_extend_enabled = False
        worker.paused = False
        worker.overwrite_task_def = True
        worker.strict_schema = False
        
        config = Configuration(server_api_url='http://localhost:8080/api')
        runner = TaskRunner(worker, configuration=config)
        
        assert len(runner.configurations) == 1
        assert len(runner.task_clients) == 1
        assert len(runner._auth_failures) == 1
    
    def test_task_runner_multiple_configs(self):
        """TaskRunner with multiple configurations."""
        from conductor.client.automator.task_runner import TaskRunner
        from conductor.client.worker.worker_interface import WorkerInterface
        
        worker = MagicMock(spec=WorkerInterface)
        worker.get_task_definition_name.return_value = 'test_task'
        worker.task_definition_names = ['test_task']
        worker.thread_count = 2
        worker.poll_interval = 1
        worker.domain = None
        worker.worker_id = 'test-worker'
        worker.register_task_def = False
        worker.poll_timeout = 100
        worker.lease_extend_enabled = False
        worker.paused = False
        worker.overwrite_task_def = True
        worker.strict_schema = False
        
        configs = [
            Configuration(server_api_url='http://east:8080/api'),
            Configuration(server_api_url='http://west:8080/api')
        ]
        runner = TaskRunner(worker, configuration=configs)
        
        assert len(runner.configurations) == 2
        assert len(runner.task_clients) == 2
        assert len(runner._auth_failures) == 2
        assert len(runner._last_auth_failure) == 2
    
    def test_async_task_runner_multiple_configs(self):
        """AsyncTaskRunner with multiple configurations."""
        from conductor.client.automator.async_task_runner import AsyncTaskRunner
        from conductor.client.worker.worker_interface import WorkerInterface
        
        worker = MagicMock(spec=WorkerInterface)
        worker.get_task_definition_name.return_value = 'test_task'
        worker.task_definition_names = ['test_task']
        worker.thread_count = 2
        worker.poll_interval = 1
        worker.domain = None
        worker.worker_id = 'test-worker'
        worker.register_task_def = False
        worker.poll_timeout = 100
        worker.lease_extend_enabled = False
        worker.paused = False
        worker.overwrite_task_def = True
        worker.strict_schema = False
        
        configs = [
            Configuration(server_api_url='http://east:8080/api'),
            Configuration(server_api_url='http://west:8080/api')
        ]
        runner = AsyncTaskRunner(worker, configuration=configs)
        
        assert len(runner.configurations) == 2
        assert len(runner._auth_failures) == 2
        # async_task_clients created in run(), not __init__
        assert runner.async_task_clients == []


class TestCircuitBreaker:
    """Tests for circuit breaker functionality in multi-homed mode."""
    
    def test_task_runner_circuit_breaker_initialized(self):
        """TaskRunner initializes circuit breaker state."""
        from conductor.client.automator.task_runner import TaskRunner
        from conductor.client.worker.worker_interface import WorkerInterface
        
        worker = MagicMock(spec=WorkerInterface)
        worker.get_task_definition_name.return_value = 'test_task'
        worker.task_definition_names = ['test_task']
        worker.thread_count = 2
        worker.poll_interval = 1
        worker.domain = None
        worker.worker_id = 'test-worker'
        worker.register_task_def = False
        worker.poll_timeout = 100
        worker.lease_extend_enabled = False
        worker.paused = False
        worker.overwrite_task_def = True
        worker.strict_schema = False
        
        configs = [
            Configuration(server_api_url='http://east:8080/api'),
            Configuration(server_api_url='http://west:8080/api')
        ]
        runner = TaskRunner(worker, configuration=configs)
        
        # Circuit breaker state initialized
        assert hasattr(runner, '_server_failures')
        assert hasattr(runner, '_circuit_open_until')
        assert len(runner._server_failures) == 2
        assert len(runner._circuit_open_until) == 2
        assert all(f == 0 for f in runner._server_failures)
        assert all(t == 0.0 for t in runner._circuit_open_until)
        
        # Constants defined
        assert runner._CIRCUIT_FAILURE_THRESHOLD == 3
        assert runner._CIRCUIT_RESET_SECONDS == 30
        assert runner._POLL_TIMEOUT_SECONDS == 5
    
    def test_task_runner_poll_executor_for_multi_homed(self):
        """TaskRunner creates poll executor only for multi-homed mode."""
        from conductor.client.automator.task_runner import TaskRunner
        from conductor.client.worker.worker_interface import WorkerInterface
        
        worker = MagicMock(spec=WorkerInterface)
        worker.get_task_definition_name.return_value = 'test_task'
        worker.task_definition_names = ['test_task']
        worker.thread_count = 2
        worker.poll_interval = 1
        worker.domain = None
        worker.worker_id = 'test-worker'
        worker.register_task_def = False
        worker.poll_timeout = 100
        worker.lease_extend_enabled = False
        worker.paused = False
        worker.overwrite_task_def = True
        worker.strict_schema = False
        
        # Single server - no poll executor
        single_config = Configuration(server_api_url='http://localhost:8080/api')
        runner_single = TaskRunner(worker, configuration=single_config)
        assert runner_single._poll_executor is None
        
        # Multi-homed - poll executor created
        multi_configs = [
            Configuration(server_api_url='http://east:8080/api'),
            Configuration(server_api_url='http://west:8080/api')
        ]
        runner_multi = TaskRunner(worker, configuration=multi_configs)
        assert runner_multi._poll_executor is not None
    
    def test_async_task_runner_circuit_breaker_initialized(self):
        """AsyncTaskRunner initializes circuit breaker state."""
        from conductor.client.automator.async_task_runner import AsyncTaskRunner
        from conductor.client.worker.worker_interface import WorkerInterface
        
        worker = MagicMock(spec=WorkerInterface)
        worker.get_task_definition_name.return_value = 'test_task'
        worker.task_definition_names = ['test_task']
        worker.thread_count = 2
        worker.poll_interval = 1
        worker.domain = None
        worker.worker_id = 'test-worker'
        worker.register_task_def = False
        worker.poll_timeout = 100
        worker.lease_extend_enabled = False
        worker.paused = False
        worker.overwrite_task_def = True
        worker.strict_schema = False
        
        configs = [
            Configuration(server_api_url='http://east:8080/api'),
            Configuration(server_api_url='http://west:8080/api')
        ]
        runner = AsyncTaskRunner(worker, configuration=configs)
        
        # Circuit breaker state initialized
        assert hasattr(runner, '_server_failures')
        assert hasattr(runner, '_circuit_open_until')
        assert len(runner._server_failures) == 2
        assert len(runner._circuit_open_until) == 2
        
        # Constants defined
        assert runner._CIRCUIT_FAILURE_THRESHOLD == 3
        assert runner._CIRCUIT_RESET_SECONDS == 30
        assert runner._POLL_TIMEOUT_SECONDS == 5


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility with existing code."""
    
    def test_task_handler_single_config_kwarg(self):
        """TaskHandler accepts single config as keyword arg."""
        from conductor.client.automator.task_handler import TaskHandler
        
        config = Configuration(server_api_url='http://localhost:8080/api')
        
        # Should not raise
        handler = TaskHandler(workers=[], configuration=config, scan_for_annotated_workers=False)
        assert len(handler.configurations) == 1
    
    def test_task_handler_no_config_uses_env(self):
        """TaskHandler with no config uses from_env_multi()."""
        from conductor.client.automator.task_handler import TaskHandler
        
        with patch.dict(os.environ, {
            'CONDUCTOR_SERVER_URL': 'https://server1.example.com/api,https://server2.example.com/api'
        }, clear=True):
            handler = TaskHandler(workers=[], scan_for_annotated_workers=False)
            assert len(handler.configurations) == 2
    
    def test_configuration_single_server_unchanged(self):
        """Single server Configuration() behavior unchanged."""
        config = Configuration(server_api_url='http://localhost:8080/api')
        assert config.host == 'http://localhost:8080/api'
    
    def test_configuration_env_var_single_unchanged(self):
        """Single CONDUCTOR_SERVER_URL still works."""
        with patch.dict(os.environ, {
            'CONDUCTOR_SERVER_URL': 'http://myserver:8080/api'
        }, clear=True):
            config = Configuration()
            assert config.host == 'http://myserver:8080/api'
