import unittest
import json
from conductor.client.http.models.workflow_schedule_execution_model import WorkflowScheduleExecutionModel
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestWorkflowScheduleExecutionModelSerDes(unittest.TestCase):
    def setUp(self):
        # Load the JSON template
        self.server_json_str = JsonTemplateResolver.get_json_string("WorkflowScheduleExecutionModel")
        self.server_json = json.loads(self.server_json_str)

    def test_workflow_schedule_execution_model_serdes(self):
        # 1. Deserialize JSON into model object
        model = WorkflowScheduleExecutionModel(
            execution_id=self.server_json.get('executionId'),
            schedule_name=self.server_json.get('scheduleName'),
            scheduled_time=self.server_json.get('scheduledTime'),
            execution_time=self.server_json.get('executionTime'),
            workflow_name=self.server_json.get('workflowName'),
            workflow_id=self.server_json.get('workflowId'),
            reason=self.server_json.get('reason'),
            stack_trace=self.server_json.get('stackTrace'),
            start_workflow_request=self.server_json.get('startWorkflowRequest'),
            state=self.server_json.get('state'),
            zone_id=self.server_json.get('zoneId'),
            org_id=self.server_json.get('orgId')
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(model.execution_id, self.server_json.get('executionId'))
        self.assertEqual(model.schedule_name, self.server_json.get('scheduleName'))
        self.assertEqual(model.scheduled_time, self.server_json.get('scheduledTime'))
        self.assertEqual(model.execution_time, self.server_json.get('executionTime'))
        self.assertEqual(model.workflow_name, self.server_json.get('workflowName'))
        self.assertEqual(model.workflow_id, self.server_json.get('workflowId'))
        self.assertEqual(model.reason, self.server_json.get('reason'))
        self.assertEqual(model.stack_trace, self.server_json.get('stackTrace'))
        self.assertEqual(model.start_workflow_request, self.server_json.get('startWorkflowRequest'))
        self.assertEqual(model.state, self.server_json.get('state'))
        self.assertEqual(model.zone_id, self.server_json.get('zoneId'))
        self.assertEqual(model.org_id, self.server_json.get('orgId'))

        # Check that enum values are correctly handled
        if model.state:
            self.assertIn(model.state, ["POLLED", "FAILED", "EXECUTED"])

        # 3. Serialize model back to dict
        model_dict = model.to_dict()

        # 4. Compare with original JSON to ensure no data loss
        # Handle camelCase to snake_case transformations
        self.assertEqual(model_dict.get('execution_id'), self.server_json.get('executionId'))
        self.assertEqual(model_dict.get('schedule_name'), self.server_json.get('scheduleName'))
        self.assertEqual(model_dict.get('scheduled_time'), self.server_json.get('scheduledTime'))
        self.assertEqual(model_dict.get('execution_time'), self.server_json.get('executionTime'))
        self.assertEqual(model_dict.get('workflow_name'), self.server_json.get('workflowName'))
        self.assertEqual(model_dict.get('workflow_id'), self.server_json.get('workflowId'))
        self.assertEqual(model_dict.get('reason'), self.server_json.get('reason'))
        self.assertEqual(model_dict.get('stack_trace'), self.server_json.get('stackTrace'))
        self.assertEqual(model_dict.get('start_workflow_request'), self.server_json.get('startWorkflowRequest'))
        self.assertEqual(model_dict.get('state'), self.server_json.get('state'))
        self.assertEqual(model_dict.get('zone_id'), self.server_json.get('zoneId'))
        self.assertEqual(model_dict.get('org_id'), self.server_json.get('orgId'))

        # Additional validation for complex structures (if any were present)
        if isinstance(model.start_workflow_request, dict):
            self.assertEqual(model_dict.get('start_workflow_request'), self.server_json.get('startWorkflowRequest'))


if __name__ == '__main__':
    unittest.main()