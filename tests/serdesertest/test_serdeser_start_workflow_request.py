import unittest
import json
from conductor.client.http.models.start_workflow_request import StartWorkflowRequest, IdempotencyStrategy
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestStartWorkflowRequestSerDeSer(unittest.TestCase):

    def setUp(self):
        # Load JSON template string
        self.server_json_str = JsonTemplateResolver.get_json_string("StartWorkflowRequest")
        self.server_json = json.loads(self.server_json_str)

    def test_deserialize_serialize_start_workflow_request(self):
        # 1. Deserialize JSON into model object
        workflow_request = StartWorkflowRequest(
            name=self.server_json.get('name'),
            version=self.server_json.get('version'),
            correlation_id=self.server_json.get('correlationId'),
            input=self.server_json.get('input'),
            task_to_domain=self.server_json.get('taskToDomain'),
            workflow_def=self.server_json.get('workflowDef'),
            external_input_payload_storage_path=self.server_json.get('externalInputPayloadStoragePath'),
            priority=self.server_json.get('priority'),
            created_by=self.server_json.get('createdBy'),
            idempotency_key=self.server_json.get('idempotencyKey'),
            idempotency_strategy=IdempotencyStrategy(self.server_json.get('idempotencyStrategy', 'FAIL'))
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(self.server_json.get('name'), workflow_request.name)
        self.assertEqual(self.server_json.get('version'), workflow_request.version)
        self.assertEqual(self.server_json.get('correlationId'), workflow_request.correlation_id)

        # Verify dictionaries (maps)
        self.assertEqual(self.server_json.get('input'), workflow_request.input)
        self.assertEqual(self.server_json.get('taskToDomain'), workflow_request.task_to_domain)

        # Verify complex object
        self.assertEqual(self.server_json.get('workflowDef'), workflow_request.workflow_def)

        # Verify other fields
        self.assertEqual(self.server_json.get('externalInputPayloadStoragePath'),
                         workflow_request.external_input_payload_storage_path)
        self.assertEqual(self.server_json.get('priority'), workflow_request.priority)
        self.assertEqual(self.server_json.get('createdBy'), workflow_request.created_by)

        # Verify enum field
        self.assertEqual(self.server_json.get('idempotencyKey'), workflow_request.idempotency_key)
        expected_strategy = IdempotencyStrategy(self.server_json.get('idempotencyStrategy', 'FAIL'))
        self.assertEqual(expected_strategy, workflow_request.idempotency_strategy)

        # 3. Serialize model back to dictionary
        result_dict = workflow_request.to_dict()

        # 4. Verify the result matches the original JSON
        # Handle camelCase to snake_case transformations
        self.assertEqual(self.server_json.get('name'), result_dict.get('name'))
        self.assertEqual(self.server_json.get('version'), result_dict.get('version'))
        self.assertEqual(self.server_json.get('correlationId'), result_dict.get('correlation_id'))
        self.assertEqual(self.server_json.get('input'), result_dict.get('input'))
        self.assertEqual(self.server_json.get('taskToDomain'), result_dict.get('task_to_domain'))
        self.assertEqual(self.server_json.get('workflowDef'), result_dict.get('workflow_def'))
        self.assertEqual(self.server_json.get('externalInputPayloadStoragePath'),
                         result_dict.get('external_input_payload_storage_path'))
        self.assertEqual(self.server_json.get('priority'), result_dict.get('priority'))
        self.assertEqual(self.server_json.get('createdBy'), result_dict.get('created_by'))
        self.assertEqual(self.server_json.get('idempotencyKey'), result_dict.get('idempotency_key'))

        # For the enum, verify the string representation
        expected_strategy_str = self.server_json.get('idempotencyStrategy', 'FAIL')
        if isinstance(expected_strategy_str, tuple):
            expected_strategy_str = expected_strategy_str[0]
        self.assertEqual(expected_strategy_str, str(result_dict.get('idempotency_strategy')))


if __name__ == '__main__':
    unittest.main()