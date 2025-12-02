"""
Tests for Automatic Task Definition Registration

Tests the register_task_def functionality including:
- Task definition registration
- JSON Schema generation and registration
- Conflict handling (existing tasks/schemas)
- Error handling and graceful degradation
- Both TaskRunner and AsyncTaskRunner
"""

import asyncio
import os
import unittest
from dataclasses import dataclass
from typing import Optional, List, Dict, Union
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from conductor.client.automator.task_runner import TaskRunner
from conductor.client.automator.async_task_runner import AsyncTaskRunner
from conductor.client.configuration.configuration import Configuration
from conductor.client.context.task_context import TaskInProgress
from conductor.client.http.models.task_def import TaskDef
from conductor.client.http.models.schema_def import SchemaDef, SchemaType
from conductor.client.worker.worker import Worker


def setup_update_then_register_mock(mock_metadata):
    """
    Helper to set up mock for update-first, register-fallback pattern.

    Simulates:
    - First call (update_task_def): Fails with "Not found" (task doesn't exist)
    - Second call (register_task_def): Succeeds (creates new task)
    """
    # update fails (task doesn't exist yet)
    mock_metadata.update_task_def.side_effect = Exception("Not found")
    # register succeeds
    mock_metadata.register_task_def.return_value = None


def get_registered_or_updated_task_def(mock_metadata):
    """Get TaskDef from either update_task_def or register_task_def call."""
    if mock_metadata.update_task_def.called:
        return mock_metadata.update_task_def.call_args[1]['task_def']
    elif mock_metadata.register_task_def.called:
        return mock_metadata.register_task_def.call_args[1]['task_def']
    else:
        return None


class TestTaskRunnerRegistration(unittest.TestCase):
    """Test task registration in TaskRunner (sync workers)."""

    def setUp(self):
        self.config = Configuration()

    def test_register_task_def_disabled_by_default(self):
        """When register_task_def=False, no registration should occur."""

        def simple_worker(name: str) -> str:
            return f"Hello {name}"

        worker = Worker(
            task_definition_name='greet',
            execute_function=simple_worker,
            register_task_def=False  # Disabled
        )

        with patch('conductor.client.automator.task_runner.OrkesMetadataClient') as mock_metadata:
            task_runner = TaskRunner(worker, self.config)

            # Metadata client should not be called
            mock_metadata.assert_not_called()

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    @patch('conductor.client.automator.task_runner.OrkesSchemaClient')
    def test_successful_registration_with_schemas(self, mock_schema_client_class, mock_metadata_client_class):
        """Test successful registration of task + schemas."""

        @dataclass
        class OrderInfo:
            order_id: str
            amount: float

        def process_order(order: OrderInfo) -> dict:
            return {'status': 'processed'}

        worker = Worker(
            task_definition_name='process_order',
            execute_function=process_order,
            register_task_def=True
        )

        # Setup mocks
        mock_metadata = Mock()
        mock_schema = Mock()
        mock_metadata_client_class.return_value = mock_metadata
        mock_schema_client_class.return_value = mock_schema

        # Setup update-first, register-fallback pattern
        setup_update_then_register_mock(mock_metadata)

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Verify metadata client was created
        mock_metadata_client_class.assert_called_once_with(self.config)

        # Verify schema client was created
        mock_schema_client_class.return_value = mock_schema

        # Verify schemas were registered (2 calls: input and output)
        self.assertEqual(mock_schema.register_schema.call_count, 2)

        # Verify task definition was registered or updated
        self.assertTrue(mock_metadata.update_task_def.called or mock_metadata.register_task_def.called)

        # Get the TaskDef that was registered/updated
        registered_task_def = get_registered_or_updated_task_def(mock_metadata)
        self.assertEqual(registered_task_def.name, 'process_order')
        self.assertIsNotNone(registered_task_def.input_schema)
        self.assertIsNotNone(registered_task_def.output_schema)

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    def test_updates_existing_task_definition(self, mock_metadata_client_class):
        """When task exists, updates it (overwrites)."""

        def worker_func(name: str) -> str:
            return name

        worker = Worker(
            task_definition_name='existing_task',
            execute_function=worker_func,
            register_task_def=True
        )

        mock_metadata = Mock()
        mock_metadata_client_class.return_value = mock_metadata

        # update_task_def succeeds (task exists)
        mock_metadata.update_task_def.return_value = None

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Should call update_task_def
        mock_metadata.update_task_def.assert_called_once()

        # Get the updated TaskDef
        updated_task_def = mock_metadata.update_task_def.call_args[1]['task_def']
        self.assertEqual(updated_task_def.name, 'existing_task')

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    @patch('conductor.client.automator.task_runner.OrkesSchemaClient')
    def test_always_registers_schemas(self, mock_schema_client_class, mock_metadata_client_class):
        """Schemas are always registered (may overwrite existing)."""

        def worker_func(name: str) -> str:
            return name

        worker = Worker(
            task_definition_name='task_with_schemas',
            execute_function=worker_func,
            register_task_def=True
        )

        mock_metadata = Mock()
        mock_schema = Mock()
        mock_metadata_client_class.return_value = mock_metadata
        mock_schema_client_class.return_value = mock_schema

        # Task doesn't exist
        setup_update_then_register_mock(mock_metadata)

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Should always register schemas (2 calls: input and output)
        self.assertEqual(mock_schema.register_schema.call_count, 2)

        # Should register task definition
        self.assertTrue(mock_metadata.update_task_def.called or mock_metadata.register_task_def.called)

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    def test_registration_without_type_hints(self, mock_metadata_client_class):
        """When function has no type hints, register task without schemas."""

        def no_hints(data):
            return data

        worker = Worker(
            task_definition_name='no_hints_task',
            execute_function=no_hints,
            register_task_def=True
        )

        mock_metadata = Mock()
        mock_metadata_client_class.return_value = mock_metadata
        setup_update_then_register_mock(mock_metadata)

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Should register task definition
        self.assertTrue(mock_metadata.update_task_def.called or mock_metadata.register_task_def.called)

        # TaskDef should have no schemas
        registered_task_def = get_registered_or_updated_task_def(mock_metadata)
        self.assertEqual(registered_task_def.name, 'no_hints_task')
        self.assertIsNone(registered_task_def.input_schema)
        self.assertIsNone(registered_task_def.output_schema)

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    def test_registration_failure_doesnt_crash_worker(self, mock_metadata_client_class):
        """When registration fails, worker should continue (graceful degradation)."""

        def worker_func(name: str) -> str:
            return name

        worker = Worker(
            task_definition_name='failing_task',
            execute_function=worker_func,
            register_task_def=True
        )

        mock_metadata = Mock()
        mock_metadata_client_class.return_value = mock_metadata

        # All API calls fail
        mock_metadata.get_task_def.side_effect = Exception("API Error")
        mock_metadata.register_task_def.side_effect = Exception("Registration failed")

        task_runner = TaskRunner(worker, self.config)

        # Should not crash - just log warning
        try:
            task_runner._TaskRunner__register_task_definition()
        except Exception as e:
            self.fail(f"Registration failure should not crash worker: {e}")

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    @patch('conductor.client.automator.task_runner.OrkesSchemaClient')
    def test_schema_registration_validates_draft07(self, mock_schema_client_class, mock_metadata_client_class):
        """Verify registered schemas are JSON Schema draft-07."""

        def worker_func(user_id: str, count: int = 10) -> dict:
            return {}

        worker = Worker(
            task_definition_name='test_task',
            execute_function=worker_func,
            register_task_def=True
        )

        mock_metadata = Mock()
        mock_schema = Mock()
        mock_metadata_client_class.return_value = mock_metadata
        mock_schema_client_class.return_value = mock_schema

        setup_update_then_register_mock(mock_metadata)
        mock_schema.get_schema.side_effect = Exception("Not found")

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Get the registered schemas
        schema_calls = mock_schema.register_schema.call_args_list
        self.assertEqual(len(schema_calls), 2)  # Input and output

        # Verify input schema
        input_schema_def = schema_calls[0][0][0]  # First call, first arg
        self.assertEqual(input_schema_def.name, 'test_task_input')
        self.assertEqual(input_schema_def.version, 1)
        self.assertEqual(input_schema_def.type, SchemaType.JSON)
        self.assertIn('$schema', input_schema_def.data)
        self.assertEqual(input_schema_def.data['$schema'], 'http://json-schema.org/draft-07/schema#')

        # Verify output schema
        output_schema_def = schema_calls[1][0][0]  # Second call, first arg
        self.assertEqual(output_schema_def.name, 'test_task_output')
        self.assertEqual(output_schema_def.version, 1)
        self.assertEqual(output_schema_def.type, SchemaType.JSON)


class TestAsyncTaskRunnerRegistration(unittest.TestCase):
    """Test task registration in AsyncTaskRunner (async workers)."""

    def setUp(self):
        self.config = Configuration()

    @patch('conductor.client.automator.async_task_runner.OrkesMetadataClient')
    @patch('conductor.client.automator.async_task_runner.OrkesSchemaClient')
    def test_async_worker_registration(self, mock_schema_client_class, mock_metadata_client_class):
        """Test registration works for async workers."""

        async def async_worker(url: str) -> dict:
            return {'data': 'result'}

        worker = Worker(
            task_definition_name='fetch_data',
            execute_function=async_worker,
            register_task_def=True
        )

        mock_metadata = Mock()
        mock_schema = Mock()
        mock_metadata_client_class.return_value = mock_metadata
        mock_schema_client_class.return_value = mock_schema

        setup_update_then_register_mock(mock_metadata)
        mock_schema.get_schema.side_effect = Exception("Not found")

        async_task_runner = AsyncTaskRunner(worker, self.config)

        # Run registration
        asyncio.run(async_task_runner._AsyncTaskRunner__async_register_task_definition())

        # Verify registration occurred
        self.assertTrue(mock_metadata.update_task_def.called or mock_metadata.register_task_def.called)
        registered_task_def = get_registered_or_updated_task_def(mock_metadata)
        self.assertEqual(registered_task_def.name, 'fetch_data')

    @patch('conductor.client.automator.async_task_runner.OrkesMetadataClient')
    def test_async_updates_existing_task(self, mock_metadata_client_class):
        """Async runner should update existing task (overwrites)."""

        async def async_worker(name: str) -> str:
            return name

        worker = Worker(
            task_definition_name='existing_async_task',
            execute_function=async_worker,
            register_task_def=True
        )

        mock_metadata = Mock()
        mock_metadata_client_class.return_value = mock_metadata

        # update_task_def succeeds (task exists)
        mock_metadata.update_task_def.return_value = None

        async_task_runner = AsyncTaskRunner(worker, self.config)
        asyncio.run(async_task_runner._AsyncTaskRunner__async_register_task_definition())

        # Should call update_task_def
        mock_metadata.update_task_def.assert_called_once()


class TestSchemaLinking(unittest.TestCase):
    """Test that task definitions correctly link to schemas."""

    def setUp(self):
        self.config = Configuration()

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    @patch('conductor.client.automator.task_runner.OrkesSchemaClient')
    def test_task_def_links_to_schemas(self, mock_schema_client_class, mock_metadata_client_class):
        """Task definition should reference created schemas."""

        def worker_func(user_id: str) -> dict:
            return {}

        worker = Worker(
            task_definition_name='my_task',
            execute_function=worker_func,
            register_task_def=True
        )

        mock_metadata = Mock()
        mock_schema = Mock()
        mock_metadata_client_class.return_value = mock_metadata
        mock_schema_client_class.return_value = mock_schema

        setup_update_then_register_mock(mock_metadata)
        mock_schema.get_schema.side_effect = Exception("Not found")

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Get registered TaskDef
        task_def = get_registered_or_updated_task_def(mock_metadata)

        # Verify schema links
        self.assertEqual(task_def.input_schema, {"name": "my_task_input", "version": 1})
        self.assertEqual(task_def.output_schema, {"name": "my_task_output", "version": 1})

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    def test_task_def_without_schemas_when_no_hints(self, mock_metadata_client_class):
        """Task def should have no schema links when type hints unavailable."""

        def no_hints(data):
            return data

        worker = Worker(
            task_definition_name='no_schema_task',
            execute_function=no_hints,
            register_task_def=True
        )

        mock_metadata = Mock()
        mock_metadata_client_class.return_value = mock_metadata
        setup_update_then_register_mock(mock_metadata)

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Get registered TaskDef
        task_def = get_registered_or_updated_task_def(mock_metadata)

        # Should have no schema links
        self.assertIsNone(task_def.input_schema)
        self.assertIsNone(task_def.output_schema)


class TestErrorHandling(unittest.TestCase):
    """Test error handling during registration."""

    def setUp(self):
        self.config = Configuration()

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    def test_metadata_client_creation_failure(self, mock_metadata_client_class):
        """When metadata client creation fails, worker continues."""

        def worker_func(name: str) -> str:
            return name

        worker = Worker(
            task_definition_name='test_task',
            execute_function=worker_func,
            register_task_def=True
        )

        # Metadata client creation fails
        mock_metadata_client_class.side_effect = Exception("Auth failed")

        task_runner = TaskRunner(worker, self.config)

        # Should not crash
        try:
            task_runner._TaskRunner__register_task_definition()
        except Exception as e:
            self.fail(f"Worker should continue even if registration fails: {e}")

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    @patch('conductor.client.automator.task_runner.OrkesSchemaClient')
    def test_schema_registration_failure_continues(self, mock_schema_client_class, mock_metadata_client_class):
        """When schema registration fails, still register task (without schemas)."""

        def worker_func(name: str) -> str:
            return name

        worker = Worker(
            task_definition_name='test_task',
            execute_function=worker_func,
            register_task_def=True
        )

        mock_metadata = Mock()
        mock_schema = Mock()
        mock_metadata_client_class.return_value = mock_metadata
        mock_schema_client_class.return_value = mock_schema

        setup_update_then_register_mock(mock_metadata)
        mock_schema.get_schema.side_effect = Exception("Not found")

        # Schema registration fails
        mock_schema.register_schema.side_effect = Exception("Schema save failed")

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Should still register task (without schemas)
        self.assertTrue(mock_metadata.update_task_def.called or mock_metadata.register_task_def.called)

        # TaskDef should have no schemas (registration failed)
        task_def = get_registered_or_updated_task_def(mock_metadata)
        self.assertIsNone(task_def.input_schema)
        self.assertIsNone(task_def.output_schema)


class TestComplexDataTypes(unittest.TestCase):
    """Test registration with complex Python types."""

    def setUp(self):
        self.config = Configuration()

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    @patch('conductor.client.automator.task_runner.OrkesSchemaClient')
    def test_nested_dataclass_registration(self, mock_schema_client_class, mock_metadata_client_class):
        """Test registration with nested dataclasses."""

        @dataclass
        class Address:
            street: str
            city: str

        @dataclass
        class User:
            name: str
            address: Address

        def update_user(user: User) -> dict:
            return {}

        worker = Worker(
            task_definition_name='update_user',
            execute_function=update_user,
            register_task_def=True
        )

        mock_metadata = Mock()
        mock_schema = Mock()
        mock_metadata_client_class.return_value = mock_metadata
        mock_schema_client_class.return_value = mock_schema

        setup_update_then_register_mock(mock_metadata)
        mock_schema.get_schema.side_effect = Exception("Not found")

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Should register schemas
        self.assertEqual(mock_schema.register_schema.call_count, 2)

        # Get input schema
        input_schema_def = mock_schema.register_schema.call_args_list[0][0][0]
        input_schema_data = input_schema_def.data

        # Verify nested structure
        self.assertIn('user', input_schema_data['properties'])
        user_schema = input_schema_data['properties']['user']
        self.assertIn('address', user_schema['properties'])
        address_schema = user_schema['properties']['address']
        self.assertIn('street', address_schema['properties'])
        self.assertIn('city', address_schema['properties'])

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    @patch('conductor.client.automator.task_runner.OrkesSchemaClient')
    def test_union_return_type_with_task_in_progress(self, mock_schema_client_class, mock_metadata_client_class):
        """Test registration with Union[dict, TaskInProgress] return type."""

        def long_task() -> Union[dict, TaskInProgress]:
            return {}

        worker = Worker(
            task_definition_name='long_task',
            execute_function=long_task,
            register_task_def=True
        )

        mock_metadata = Mock()
        mock_schema = Mock()
        mock_metadata_client_class.return_value = mock_metadata
        mock_schema_client_class.return_value = mock_schema

        setup_update_then_register_mock(mock_metadata)
        mock_schema.get_schema.side_effect = Exception("Not found")

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Registration should complete
        self.assertTrue(mock_metadata.update_task_def.called or mock_metadata.register_task_def.called)


class TestClassBasedWorkers(unittest.TestCase):
    """Test that class-based workers (no execute_function) are handled."""

    def setUp(self):
        self.config = Configuration()

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    def test_class_worker_without_execute_function(self, mock_metadata_client_class):
        """Class-based workers don't have execute_function - should register without schemas."""

        from tests.unit.resources.workers import ClassWorker

        worker = ClassWorker('class_task')
        worker.register_task_def = True

        mock_metadata = Mock()
        mock_metadata_client_class.return_value = mock_metadata
        setup_update_then_register_mock(mock_metadata)

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Should register task without schemas
        self.assertTrue(mock_metadata.update_task_def.called or mock_metadata.register_task_def.called)

        task_def = get_registered_or_updated_task_def(mock_metadata)
        self.assertEqual(task_def.name, 'class_task')
        self.assertIsNone(task_def.input_schema)
        self.assertIsNone(task_def.output_schema)


if __name__ == '__main__':
    unittest.main()


class TestOverwriteTaskDefFlag(unittest.TestCase):
    """Test overwrite_task_def configuration flag."""

    def setUp(self):
        self.config = Configuration()

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    def test_overwrite_true_always_updates(self, mock_metadata_client_class):
        """When overwrite_task_def=True, should call update_task_def."""

        def worker_func(name: str) -> str:
            return name

        worker = Worker(
            task_definition_name='my_task',
            execute_function=worker_func,
            register_task_def=True,
            overwrite_task_def=True  # Should update
        )

        mock_metadata = Mock()
        mock_metadata_client_class.return_value = mock_metadata
        mock_metadata.update_task_def.return_value = None

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Should call update (overwrites)
        mock_metadata.update_task_def.assert_called_once()

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    def test_overwrite_false_checks_existence(self, mock_metadata_client_class):
        """When overwrite_task_def=False, should check if task exists first."""

        def worker_func(name: str) -> str:
            return name

        worker = Worker(
            task_definition_name='existing_task',
            execute_function=worker_func,
            register_task_def=True,
            overwrite_task_def=False  # Should check first
        )

        mock_metadata = Mock()
        mock_metadata_client_class.return_value = mock_metadata

        # Task exists
        existing_task = TaskDef(name='existing_task')
        mock_metadata.get_task_def.return_value = existing_task

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Should check if task exists
        mock_metadata.get_task_def.assert_called_once_with('existing_task')

        # Should NOT call update or register
        mock_metadata.update_task_def.assert_not_called()
        mock_metadata.register_task_def.assert_not_called()

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    def test_overwrite_false_creates_if_not_exists(self, mock_metadata_client_class):
        """When overwrite_task_def=False and task doesn't exist, should create."""

        def worker_func(name: str) -> str:
            return name

        worker = Worker(
            task_definition_name='new_task',
            execute_function=worker_func,
            register_task_def=True,
            overwrite_task_def=False
        )

        mock_metadata = Mock()
        mock_metadata_client_class.return_value = mock_metadata

        # Task doesn't exist
        mock_metadata.get_task_def.side_effect = Exception("Not found")

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Should check if task exists
        mock_metadata.get_task_def.assert_called_once()

        # Should call register (not update)
        mock_metadata.register_task_def.assert_called_once()

    @patch('conductor.client.automator.async_task_runner.OrkesMetadataClient')
    def test_async_worker_respects_overwrite_flag(self, mock_metadata_client_class):
        """Async workers should respect overwrite_task_def flag."""

        async def async_worker(name: str) -> str:
            return name

        # overwrite=True
        worker_overwrite = Worker(
            task_definition_name='task1',
            execute_function=async_worker,
            register_task_def=True,
            overwrite_task_def=True
        )

        mock_metadata = Mock()
        mock_metadata_client_class.return_value = mock_metadata
        mock_metadata.update_task_def.return_value = None

        async_runner = AsyncTaskRunner(worker_overwrite, self.config)
        asyncio.run(async_runner._AsyncTaskRunner__async_register_task_definition())

        # Should call update
        mock_metadata.update_task_def.assert_called_once()


class TestStrictSchemaConfiguration(unittest.TestCase):
    """Test strict_schema configuration with workers."""

    def setUp(self):
        self.config = Configuration()

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    @patch('conductor.client.automator.task_runner.OrkesSchemaClient')
    def test_strict_schema_false_generates_lenient_schemas(self, mock_schema_client_class, mock_metadata_client_class):
        """When strict_schema=False, schemas should have additionalProperties=true."""

        @dataclass
        class User:
            name: str

        def worker(user: User) -> dict:
            return {}

        worker = Worker(
            task_definition_name='test_task',
            execute_function=worker,
            register_task_def=True,
            strict_schema=False  # Lenient
        )

        mock_metadata = Mock()
        mock_schema = Mock()
        mock_metadata_client_class.return_value = mock_metadata
        mock_schema_client_class.return_value = mock_schema
        setup_update_then_register_mock(mock_metadata)

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Get registered schema
        schema_calls = mock_schema.register_schema.call_args_list
        self.assertEqual(len(schema_calls), 2)

        input_schema_def = schema_calls[0][0][0]
        input_schema_data = input_schema_def.data

        # Should be lenient
        self.assertEqual(input_schema_data['additionalProperties'], True)

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    @patch('conductor.client.automator.task_runner.OrkesSchemaClient')
    def test_strict_schema_true_generates_strict_schemas(self, mock_schema_client_class, mock_metadata_client_class):
        """When strict_schema=True, schemas should have additionalProperties=false."""

        def worker(name: str) -> str:
            return name

        worker = Worker(
            task_definition_name='strict_task',
            execute_function=worker,
            register_task_def=True,
            strict_schema=True  # Strict
        )

        mock_metadata = Mock()
        mock_schema = Mock()
        mock_metadata_client_class.return_value = mock_metadata
        mock_schema_client_class.return_value = mock_schema
        setup_update_then_register_mock(mock_metadata)

        task_runner = TaskRunner(worker, self.config)
        task_runner._TaskRunner__register_task_definition()

        # Get registered schema
        schema_calls = mock_schema.register_schema.call_args_list
        input_schema_def = schema_calls[0][0][0]
        input_schema_data = input_schema_def.data

        # Should be strict
        self.assertEqual(input_schema_data['additionalProperties'], False)


if __name__ == '__main__':
    unittest.main()


class TestEnvironmentVariableOverride(unittest.TestCase):
    """Test that overwrite_task_def and strict_schema can be overridden via env vars."""

    def setUp(self):
        self.config = Configuration()
        # Clean up any existing env vars
        for key in list(os.environ.keys()):
            if key.startswith('conductor.worker.'):
                del os.environ[key]

    def tearDown(self):
        # Clean up env vars after each test
        for key in list(os.environ.keys()):
            if key.startswith('conductor.worker.'):
                del os.environ[key]

    def test_global_env_overrides_overwrite_task_def(self):
        """Global env var should override code-level overwrite_task_def."""
        from conductor.client.worker.worker_config import resolve_worker_config

        # Set global env var
        os.environ['conductor.worker.all.overwrite_task_def'] = 'false'

        # Resolve with code-level default of True
        config = resolve_worker_config(
            worker_name='test_worker',
            overwrite_task_def=True  # Code default
        )

        # Should use env var value (False)
        self.assertEqual(config['overwrite_task_def'], False)

    def test_global_env_overrides_strict_schema(self):
        """Global env var should override code-level strict_schema."""
        from conductor.client.worker.worker_config import resolve_worker_config

        # Set global env var
        os.environ['conductor.worker.all.strict_schema'] = 'true'

        # Resolve with code-level default of False
        config = resolve_worker_config(
            worker_name='test_worker',
            strict_schema=False  # Code default
        )

        # Should use env var value (True)
        self.assertEqual(config['strict_schema'], True)

    def test_worker_specific_env_overrides_global(self):
        """Worker-specific env var should override global env var."""
        from conductor.client.worker.worker_config import resolve_worker_config

        # Set both global and worker-specific
        os.environ['conductor.worker.all.overwrite_task_def'] = 'true'
        os.environ['conductor.worker.my_worker.overwrite_task_def'] = 'false'

        config = resolve_worker_config(
            worker_name='my_worker',
            overwrite_task_def=True
        )

        # Should use worker-specific value (False)
        self.assertEqual(config['overwrite_task_def'], False)

    def test_priority_order(self):
        """Test configuration priority: worker-specific > global > code."""
        from conductor.client.worker.worker_config import resolve_worker_config

        # Set global
        os.environ['conductor.worker.all.strict_schema'] = 'true'
        os.environ['conductor.worker.all.overwrite_task_def'] = 'false'

        # Worker-specific overrides global
        os.environ['conductor.worker.priority_test.strict_schema'] = 'false'

        config = resolve_worker_config(
            worker_name='priority_test',
            overwrite_task_def=True,  # Code default
            strict_schema=False  # Code default
        )

        # strict_schema: worker-specific (False) overrides global (True)
        self.assertEqual(config['strict_schema'], False)

        # overwrite_task_def: global (False) overrides code (True)
        self.assertEqual(config['overwrite_task_def'], False)

    @patch('conductor.client.automator.task_runner.OrkesMetadataClient')
    def test_env_var_affects_actual_behavior(self, mock_metadata_client_class):
        """Env var should actually change worker behavior."""

        # Set env var to disable overwrite
        os.environ['conductor.worker.env_test.overwrite_task_def'] = 'false'

        def worker_func(name: str) -> str:
            return name

        worker = Worker(
            task_definition_name='env_test',
            execute_function=worker_func,
            register_task_def=True,
            overwrite_task_def=True  # Code says True, but env will override to False
        )

        mock_metadata = Mock()
        mock_metadata_client_class.return_value = mock_metadata

        # Existing task
        existing_task = TaskDef(name='env_test')
        mock_metadata.get_task_def.return_value = existing_task

        task_runner = TaskRunner(worker, self.config)

        # This will call __set_worker_properties which resolves env vars
        # Need to manually trigger it
        task_runner._TaskRunner__set_worker_properties()

        # Now worker should have overwrite_task_def=False from env
        self.assertEqual(worker.overwrite_task_def, False)

        # When we call registration, it should skip (because overwrite=False and task exists)
        task_runner._TaskRunner__register_task_definition()

        # Should check if task exists
        mock_metadata.get_task_def.assert_called_once()

        # Should NOT update or register (skipped because exists)
        mock_metadata.update_task_def.assert_not_called()
        mock_metadata.register_task_def.assert_not_called()


if __name__ == '__main__':
    unittest.main()


class TestUnixEnvironmentVariableFormat(unittest.TestCase):
    """Test Unix-compatible environment variable format (UPPERCASE_WITH_UNDERSCORES)."""

    def setUp(self):
        self.config = Configuration()
        # Clean up env vars
        for key in list(os.environ.keys()):
            if key.startswith('CONDUCTOR_WORKER') or key.startswith('conductor.worker'):
                del os.environ[key]

    def tearDown(self):
        # Clean up env vars
        for key in list(os.environ.keys()):
            if key.startswith('CONDUCTOR_WORKER') or key.startswith('conductor.worker'):
                del os.environ[key]

    def test_unix_format_global_all(self):
        """CONDUCTOR_WORKER_ALL_* format should work for global config."""
        from conductor.client.worker.worker_config import resolve_worker_config

        # Set using Unix format
        os.environ['CONDUCTOR_WORKER_ALL_STRICT_SCHEMA'] = 'true'
        os.environ['CONDUCTOR_WORKER_ALL_OVERWRITE_TASK_DEF'] = 'false'

        config = resolve_worker_config(
            worker_name='test_worker',
            strict_schema=False,
            overwrite_task_def=True
        )

        # Should use env values
        self.assertEqual(config['strict_schema'], True)
        self.assertEqual(config['overwrite_task_def'], False)

    def test_unix_format_worker_specific(self):
        """CONDUCTOR_WORKER_TASKNAME_* format should work for worker-specific config."""
        from conductor.client.worker.worker_config import resolve_worker_config

        # Set using Unix format
        os.environ['CONDUCTOR_WORKER_MY_TASK_STRICT_SCHEMA'] = 'true'
        os.environ['CONDUCTOR_WORKER_MY_TASK_OVERWRITE_TASK_DEF'] = 'false'

        config = resolve_worker_config(
            worker_name='my_task',
            strict_schema=False,
            overwrite_task_def=True
        )

        # Should use env values
        self.assertEqual(config['strict_schema'], True)
        self.assertEqual(config['overwrite_task_def'], False)

    def test_unix_format_priority(self):
        """Worker-specific Unix format should override global Unix format."""
        from conductor.client.worker.worker_config import resolve_worker_config

        # Set both global and worker-specific
        os.environ['CONDUCTOR_WORKER_ALL_STRICT_SCHEMA'] = 'true'
        os.environ['CONDUCTOR_WORKER_PRIORITY_TEST_STRICT_SCHEMA'] = 'false'

        config = resolve_worker_config(
            worker_name='priority_test',
            strict_schema=True  # Code default
        )

        # Should use worker-specific value (False), not global (True)
        self.assertEqual(config['strict_schema'], False)


if __name__ == '__main__':
    unittest.main()
