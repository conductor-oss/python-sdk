import unittest
import json
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver
from conductor.client.http.models.task_summary import TaskSummary


class TestTaskSummarySerDeser(unittest.TestCase):
    def setUp(self):
        # Load JSON template
        self.server_json_str = JsonTemplateResolver.get_json_string("TaskSummary")
        self.server_json = json.loads(self.server_json_str)

    def test_task_summary_ser_deser(self):
        # 1. Deserialize JSON to TaskSummary object
        task_summary = TaskSummary(
            workflow_id=self.server_json.get('workflowId'),
            workflow_type=self.server_json.get('workflowType'),
            correlation_id=self.server_json.get('correlationId'),
            scheduled_time=self.server_json.get('scheduledTime'),
            start_time=self.server_json.get('startTime'),
            update_time=self.server_json.get('updateTime'),
            end_time=self.server_json.get('endTime'),
            status=self.server_json.get('status'),
            reason_for_incompletion=self.server_json.get('reasonForIncompletion'),
            execution_time=self.server_json.get('executionTime'),
            queue_wait_time=self.server_json.get('queueWaitTime'),
            task_def_name=self.server_json.get('taskDefName'),
            task_type=self.server_json.get('taskType'),
            input=self.server_json.get('input'),
            output=self.server_json.get('output'),
            task_id=self.server_json.get('taskId'),
            external_input_payload_storage_path=self.server_json.get('externalInputPayloadStoragePath'),
            external_output_payload_storage_path=self.server_json.get('externalOutputPayloadStoragePath'),
            workflow_priority=self.server_json.get('workflowPriority'),
            domain=self.server_json.get('domain')
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(self.server_json.get('workflowId'), task_summary.workflow_id)
        self.assertEqual(self.server_json.get('workflowType'), task_summary.workflow_type)
        self.assertEqual(self.server_json.get('correlationId'), task_summary.correlation_id)
        self.assertEqual(self.server_json.get('scheduledTime'), task_summary.scheduled_time)
        self.assertEqual(self.server_json.get('startTime'), task_summary.start_time)
        self.assertEqual(self.server_json.get('updateTime'), task_summary.update_time)
        self.assertEqual(self.server_json.get('endTime'), task_summary.end_time)
        self.assertEqual(self.server_json.get('status'), task_summary.status)
        self.assertEqual(self.server_json.get('reasonForIncompletion'), task_summary.reason_for_incompletion)
        self.assertEqual(self.server_json.get('executionTime'), task_summary.execution_time)
        self.assertEqual(self.server_json.get('queueWaitTime'), task_summary.queue_wait_time)
        self.assertEqual(self.server_json.get('taskDefName'), task_summary.task_def_name)
        self.assertEqual(self.server_json.get('taskType'), task_summary.task_type)
        self.assertEqual(self.server_json.get('input'), task_summary.input)
        self.assertEqual(self.server_json.get('output'), task_summary.output)
        self.assertEqual(self.server_json.get('taskId'), task_summary.task_id)
        self.assertEqual(self.server_json.get('externalInputPayloadStoragePath'),
                         task_summary.external_input_payload_storage_path)
        self.assertEqual(self.server_json.get('externalOutputPayloadStoragePath'),
                         task_summary.external_output_payload_storage_path)
        self.assertEqual(self.server_json.get('workflowPriority'), task_summary.workflow_priority)
        self.assertEqual(self.server_json.get('domain'), task_summary.domain)

        # 3. Serialize TaskSummary back to JSON
        serialized_json = task_summary.to_dict()

        # 4. Verify serialized JSON matches original
        # Check that all fields from original JSON are present in serialized JSON
        for json_key, json_value in self.server_json.items():
            # Convert camelCase to snake_case for comparison
            python_key = ''.join(['_' + c.lower() if c.isupper() else c for c in json_key])
            python_key = python_key.lstrip('_')

            # Get the corresponding value from serialized JSON
            self.assertIn(python_key, serialized_json)
            self.assertEqual(json_value, serialized_json[python_key])

        # Check that all fields from serialized JSON are present in original JSON
        for python_key, python_value in serialized_json.items():
            # Convert snake_case to camelCase for comparison
            parts = python_key.split('_')
            json_key = parts[0] + ''.join(x.title() for x in parts[1:])

            # Get the corresponding value from original JSON
            self.assertIn(json_key, self.server_json)
            self.assertEqual(python_value, self.server_json[json_key])


if __name__ == '__main__':
    unittest.main()