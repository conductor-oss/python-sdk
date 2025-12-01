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
