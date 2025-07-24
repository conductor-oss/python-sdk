import unittest
import json
from conductor.client.http.models.save_schedule_request import SaveScheduleRequest
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestSaveScheduleRequestSerDes(unittest.TestCase):
    """
    Unit tests for serialization and deserialization of SaveScheduleRequest model
    """

    def setUp(self):
        # Load JSON template instead of hardcoding
        self.server_json_str = JsonTemplateResolver.get_json_string("SaveScheduleRequest")
        self.server_json = json.loads(self.server_json_str)

    def test_save_schedule_request_serde(self):
        """Test serialization and deserialization of SaveScheduleRequest model"""

        # 1. Create model object using constructor
        request = SaveScheduleRequest(
            name=self.server_json.get('name'),
            cron_expression=self.server_json.get('cronExpression'),
            run_catchup_schedule_instances=self.server_json.get('runCatchupScheduleInstances'),
            paused=self.server_json.get('paused'),
            start_workflow_request=self.server_json.get('startWorkflowRequest'),
            created_by=self.server_json.get('createdBy'),
            updated_by=self.server_json.get('updatedBy'),
            schedule_start_time=self.server_json.get('scheduleStartTime'),
            schedule_end_time=self.server_json.get('scheduleEndTime'),
            zone_id=self.server_json.get('zoneId'),
            description=self.server_json.get('description')
        )

        # 2. Verify all fields are populated correctly during creation
        self._verify_fields(request, self.server_json)

        # 3. Serialize model object back to JSON
        result_json = request.to_dict()

        # 4. Verify serialized JSON matches the original JSON
        self._verify_json_match(result_json, self.server_json)

    def _verify_fields(self, model, json_data):
        """Verify all fields in the model match their corresponding JSON values"""
        # Direct field-to-field mapping verification
        self.assertEqual(model.name, json_data.get('name'), "Field 'name' mismatch")
        self.assertEqual(model.cron_expression, json_data.get('cronExpression'), "Field 'cron_expression' mismatch")
        self.assertEqual(model.run_catchup_schedule_instances, json_data.get('runCatchupScheduleInstances'),
                         "Field 'run_catchup_schedule_instances' mismatch")
        self.assertEqual(model.paused, json_data.get('paused'), "Field 'paused' mismatch")

        # Object field handling - assuming StartWorkflowRequest is similarly structured
        # For nested objects, you might need more complex verification
        if json_data.get('startWorkflowRequest') is not None:
            self.assertIsNotNone(model.start_workflow_request, "Field 'start_workflow_request' should not be None")

        self.assertEqual(model.created_by, json_data.get('createdBy'), "Field 'created_by' mismatch")
        self.assertEqual(model.updated_by, json_data.get('updatedBy'), "Field 'updated_by' mismatch")
        self.assertEqual(model.schedule_start_time, json_data.get('scheduleStartTime'),
                         "Field 'schedule_start_time' mismatch")
        self.assertEqual(model.schedule_end_time, json_data.get('scheduleEndTime'),
                         "Field 'schedule_end_time' mismatch")
        self.assertEqual(model.zone_id, json_data.get('zoneId'), "Field 'zone_id' mismatch")
        self.assertEqual(model.description, json_data.get('description'), "Field 'description' mismatch")

    def _verify_json_match(self, result_json, original_json):
        """Verify serialized JSON matches the original JSON, accounting for camelCase/snake_case differences"""
        # Map Python snake_case to JSON camelCase for comparison
        field_mapping = {
            'name': 'name',
            'cron_expression': 'cronExpression',
            'run_catchup_schedule_instances': 'runCatchupScheduleInstances',
            'paused': 'paused',
            'start_workflow_request': 'startWorkflowRequest',
            'created_by': 'createdBy',
            'updated_by': 'updatedBy',
            'schedule_start_time': 'scheduleStartTime',
            'schedule_end_time': 'scheduleEndTime',
            'zone_id': 'zoneId',
            'description': 'description'
        }

        # Check each field to ensure it matches between result and original
        for py_field, json_field in field_mapping.items():
            # Skip comparison for None values if they don't exist in original
            if py_field in result_json and json_field in original_json:
                self.assertEqual(
                    result_json[py_field],
                    original_json[json_field],
                    f"Field mismatch: {py_field}/{json_field}"
                )


if __name__ == '__main__':
    unittest.main()