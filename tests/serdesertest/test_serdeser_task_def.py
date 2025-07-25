import unittest
import json
from conductor.client.http.models.task_def import TaskDef
from conductor.client.http.models.schema_def import SchemaDef
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestTaskDefSerDes(unittest.TestCase):
    """Test serialization and deserialization of TaskDef model."""

    def setUp(self):
        """Set up test fixtures."""
        self.server_json_str = JsonTemplateResolver.get_json_string("TaskDef")
        self.server_json = json.loads(self.server_json_str)

    def test_task_def_serdes(self):
        """Test serialization and deserialization of TaskDef model."""
        # 1. Server JSON can be correctly deserialized into SDK model object
        task_def = self._create_task_def_from_json(self.server_json)

        # 2. All fields are properly populated during deserialization
        self._verify_task_def_fields(task_def, self.server_json)

        # 3. The SDK model can be serialized back to JSON
        result_json = task_def.to_dict()

        # 4. The resulting JSON matches the original
        self._compare_json_objects(self.server_json, result_json)

    def _create_task_def_from_json(self, json_dict):
        """Create TaskDef object from JSON dictionary."""
        # Extract fields from JSON for constructor
        owner_app = json_dict.get('ownerApp')
        create_time = json_dict.get('createTime')
        update_time = json_dict.get('updateTime')
        created_by = json_dict.get('createdBy')
        updated_by = json_dict.get('updatedBy')
        name = json_dict.get('name')
        description = json_dict.get('description')
        retry_count = json_dict.get('retryCount')
        timeout_seconds = json_dict.get('timeoutSeconds')
        input_keys = json_dict.get('inputKeys')
        output_keys = json_dict.get('outputKeys')
        timeout_policy = json_dict.get('timeoutPolicy')
        retry_logic = json_dict.get('retryLogic')
        retry_delay_seconds = json_dict.get('retryDelaySeconds')
        response_timeout_seconds = json_dict.get('responseTimeoutSeconds')
        concurrent_exec_limit = json_dict.get('concurrentExecLimit')
        input_template = json_dict.get('inputTemplate')
        rate_limit_per_frequency = json_dict.get('rateLimitPerFrequency')
        rate_limit_frequency_in_seconds = json_dict.get('rateLimitFrequencyInSeconds')
        isolation_group_id = json_dict.get('isolationGroupId')
        execution_name_space = json_dict.get('executionNameSpace')
        owner_email = json_dict.get('ownerEmail')
        poll_timeout_seconds = json_dict.get('pollTimeoutSeconds')
        backoff_scale_factor = json_dict.get('backoffScaleFactor')

        # Handle nested objects
        input_schema_json = json_dict.get('inputSchema')
        input_schema_obj = None
        if input_schema_json:
            input_schema_obj = SchemaDef(
                name=input_schema_json.get('name'),
                version=input_schema_json.get('version'),
                type=input_schema_json.get('type'),
                data=input_schema_json.get('data')
            )

        output_schema_json = json_dict.get('outputSchema')
        output_schema_obj = None
        if output_schema_json:
            output_schema_obj = SchemaDef(
                name=output_schema_json.get('name'),
                version=output_schema_json.get('version'),
                type=output_schema_json.get('type'),
                data=output_schema_json.get('data')
            )

        enforce_schema = json_dict.get('enforceSchema', False)
        base_type = json_dict.get('baseType')
        total_timeout_seconds = json_dict.get('totalTimeoutSeconds')

        # Create TaskDef object using constructor
        return TaskDef(
            owner_app=owner_app,
            create_time=create_time,
            update_time=update_time,
            created_by=created_by,
            updated_by=updated_by,
            name=name,
            description=description,
            retry_count=retry_count,
            timeout_seconds=timeout_seconds,
            input_keys=input_keys,
            output_keys=output_keys,
            timeout_policy=timeout_policy,
            retry_logic=retry_logic,
            retry_delay_seconds=retry_delay_seconds,
            response_timeout_seconds=response_timeout_seconds,
            concurrent_exec_limit=concurrent_exec_limit,
            input_template=input_template,
            rate_limit_per_frequency=rate_limit_per_frequency,
            rate_limit_frequency_in_seconds=rate_limit_frequency_in_seconds,
            isolation_group_id=isolation_group_id,
            execution_name_space=execution_name_space,
            owner_email=owner_email,
            poll_timeout_seconds=poll_timeout_seconds,
            backoff_scale_factor=backoff_scale_factor,
            input_schema=input_schema_obj,
            output_schema=output_schema_obj,
            enforce_schema=enforce_schema,
            base_type=base_type,
            total_timeout_seconds=total_timeout_seconds
        )

    def _verify_task_def_fields(self, task_def, json_dict):
        """Verify all fields in TaskDef are properly populated."""
        # Verify basic fields
        self.assertEqual(task_def.owner_app, json_dict.get('ownerApp'))
        self.assertEqual(task_def.create_time, json_dict.get('createTime'))
        self.assertEqual(task_def.update_time, json_dict.get('updateTime'))
        self.assertEqual(task_def.created_by, json_dict.get('createdBy'))
        self.assertEqual(task_def.updated_by, json_dict.get('updatedBy'))
        self.assertEqual(task_def.name, json_dict.get('name'))
        self.assertEqual(task_def.description, json_dict.get('description'))
        self.assertEqual(task_def.retry_count, json_dict.get('retryCount'))
        self.assertEqual(task_def.timeout_seconds, json_dict.get('timeoutSeconds'))

        # Verify lists
        if json_dict.get('inputKeys'):
            self.assertEqual(task_def.input_keys, json_dict.get('inputKeys'))
        if json_dict.get('outputKeys'):
            self.assertEqual(task_def.output_keys, json_dict.get('outputKeys'))

        # Verify enums
        self.assertEqual(task_def.timeout_policy, json_dict.get('timeoutPolicy'))
        self.assertEqual(task_def.retry_logic, json_dict.get('retryLogic'))

        # Verify remaining fields
        self.assertEqual(task_def.retry_delay_seconds, json_dict.get('retryDelaySeconds'))
        self.assertEqual(task_def.response_timeout_seconds, json_dict.get('responseTimeoutSeconds'))
        self.assertEqual(task_def.concurrent_exec_limit, json_dict.get('concurrentExecLimit'))

        # Verify complex structures
        if json_dict.get('inputTemplate'):
            self.assertEqual(task_def.input_template, json_dict.get('inputTemplate'))

        self.assertEqual(task_def.rate_limit_per_frequency, json_dict.get('rateLimitPerFrequency'))
        self.assertEqual(task_def.rate_limit_frequency_in_seconds, json_dict.get('rateLimitFrequencyInSeconds'))
        self.assertEqual(task_def.isolation_group_id, json_dict.get('isolationGroupId'))
        self.assertEqual(task_def.execution_name_space, json_dict.get('executionNameSpace'))
        self.assertEqual(task_def.owner_email, json_dict.get('ownerEmail'))
        self.assertEqual(task_def.poll_timeout_seconds, json_dict.get('pollTimeoutSeconds'))
        self.assertEqual(task_def.backoff_scale_factor, json_dict.get('backoffScaleFactor'))

        # Verify schema objects
        if json_dict.get('inputSchema'):
            self.assertIsNotNone(task_def.input_schema)
            # Verify schema fields if needed
            input_schema_json = json_dict.get('inputSchema')
            self.assertEqual(task_def.input_schema.name, input_schema_json.get('name'))
            self.assertEqual(task_def.input_schema.type, input_schema_json.get('type'))

        if json_dict.get('outputSchema'):
            self.assertIsNotNone(task_def.output_schema)
            # Verify schema fields if needed
            output_schema_json = json_dict.get('outputSchema')
            self.assertEqual(task_def.output_schema.name, output_schema_json.get('name'))
            self.assertEqual(task_def.output_schema.type, output_schema_json.get('type'))

        self.assertEqual(task_def.enforce_schema, json_dict.get('enforceSchema', False))
        self.assertEqual(task_def.base_type, json_dict.get('baseType'))
        self.assertEqual(task_def.total_timeout_seconds, json_dict.get('totalTimeoutSeconds'))

    def _compare_json_objects(self, original, result):
        """Compare original and resulting JSON objects."""
        # Build a mapping from camelCase to snake_case for verification
        key_mapping = {}
        for attr, json_key in TaskDef.attribute_map.items():
            key_mapping[json_key] = attr

        # Check each field in the original JSON
        for camel_key, orig_value in original.items():
            # Skip if this key is not in the mapping
            if camel_key not in key_mapping:
                continue

            snake_key = key_mapping[camel_key]
            result_value = result.get(snake_key)

            # Handle special cases for nested objects
            if camel_key in ['inputSchema', 'outputSchema']:
                if orig_value is not None:
                    self.assertIsNotNone(result_value, f"Expected {snake_key} to be present in result")
                    # For schema objects, verify key properties
                    if orig_value and result_value:
                        self.assertEqual(orig_value.get('name'), result_value.get('name'))
                        self.assertEqual(orig_value.get('type'), result_value.get('type'))
                continue

            # For lists and complex objects, check existence and content
            if isinstance(orig_value, list):
                self.assertEqual(orig_value, result_value, f"List {camel_key} doesn't match")
            elif isinstance(orig_value, dict):
                if orig_value:
                    self.assertIsNotNone(result_value, f"Expected dict {snake_key} to be present in result")
                    # Check dict contents if needed
            else:
                # For simple values, verify equality
                self.assertEqual(orig_value, result_value,
                                 f"Field {camel_key} (as {snake_key}) doesn't match: {orig_value} != {result_value}")


if __name__ == '__main__':
    unittest.main()