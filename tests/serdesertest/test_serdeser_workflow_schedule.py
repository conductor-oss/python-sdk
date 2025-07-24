import unittest
from conductor.client.http.models.workflow_schedule import WorkflowSchedule
from conductor.client.http.models.start_workflow_request import StartWorkflowRequest
from conductor.client.http.models.tag_object import TagObject
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver
import json


class TestWorkflowScheduleSerialization(unittest.TestCase):
    def setUp(self):
        self.server_json_str = JsonTemplateResolver.get_json_string("WorkflowSchedule")
        self.server_json = json.loads(self.server_json_str)

    def test_workflow_schedule_serialization(self):
        # 1. Test deserialization from server JSON to SDK model
        schedule = WorkflowSchedule(
            name=self.server_json.get('name'),
            cron_expression=self.server_json.get('cronExpression'),
            run_catchup_schedule_instances=self.server_json.get('runCatchupScheduleInstances'),
            paused=self.server_json.get('paused'),
            schedule_start_time=self.server_json.get('scheduleStartTime'),
            schedule_end_time=self.server_json.get('scheduleEndTime'),
            create_time=self.server_json.get('createTime'),
            updated_time=self.server_json.get('updatedTime'),
            created_by=self.server_json.get('createdBy'),
            updated_by=self.server_json.get('updatedBy'),
            zone_id=self.server_json.get('zoneId'),
            paused_reason=self.server_json.get('pausedReason'),
            description=self.server_json.get('description')
        )

        # Process special fields that require conversion: startWorkflowRequest and tags
        if 'startWorkflowRequest' in self.server_json:
            start_req_json = self.server_json.get('startWorkflowRequest')
            if start_req_json:
                start_req = StartWorkflowRequest(
                    name=start_req_json.get('name'),
                    version=start_req_json.get('version'),
                    correlation_id=start_req_json.get('correlationId'),
                    input=start_req_json.get('input')
                )
                schedule.start_workflow_request = start_req

        if 'tags' in self.server_json:
            tags_json = self.server_json.get('tags')
            if tags_json:
                tags = []
                for tag_json in tags_json:
                    tag = TagObject(
                        key=tag_json.get('key'),
                        value=tag_json.get('value')
                    )
                    tags.append(tag)
                schedule.tags = tags

        # 2. Verify all fields are properly populated
        self._verify_all_fields(schedule, self.server_json)

        # 3. Test serialization back to JSON
        serialized_json = schedule.to_dict()

        # 4. Verify the serialized JSON matches the original
        self._verify_json_match(serialized_json, self.server_json)

    def _verify_all_fields(self, schedule, json_data):
        # Verify simple fields
        self.assertEqual(schedule.name, json_data.get('name'))
        self.assertEqual(schedule.cron_expression, json_data.get('cronExpression'))
        self.assertEqual(schedule.run_catchup_schedule_instances, json_data.get('runCatchupScheduleInstances'))
        self.assertEqual(schedule.paused, json_data.get('paused'))
        self.assertEqual(schedule.schedule_start_time, json_data.get('scheduleStartTime'))
        self.assertEqual(schedule.schedule_end_time, json_data.get('scheduleEndTime'))
        self.assertEqual(schedule.create_time, json_data.get('createTime'))
        self.assertEqual(schedule.updated_time, json_data.get('updatedTime'))
        self.assertEqual(schedule.created_by, json_data.get('createdBy'))
        self.assertEqual(schedule.updated_by, json_data.get('updatedBy'))
        self.assertEqual(schedule.zone_id, json_data.get('zoneId'))
        self.assertEqual(schedule.paused_reason, json_data.get('pausedReason'))
        self.assertEqual(schedule.description, json_data.get('description'))

        # Verify StartWorkflowRequest
        if 'startWorkflowRequest' in json_data and json_data['startWorkflowRequest'] is not None:
            start_req_json = json_data['startWorkflowRequest']
            start_req = schedule.start_workflow_request

            self.assertIsNotNone(start_req)
            self.assertEqual(start_req.name, start_req_json.get('name'))
            self.assertEqual(start_req.version, start_req_json.get('version'))
            self.assertEqual(start_req.correlation_id, start_req_json.get('correlationId'))
            self.assertEqual(start_req.input, start_req_json.get('input'))

        # Verify Tags
        if 'tags' in json_data and json_data['tags'] is not None:
            tags_json = json_data['tags']
            tags = schedule.tags

            self.assertIsNotNone(tags)
            self.assertEqual(len(tags), len(tags_json))

            for i, tag_json in enumerate(tags_json):
                tag = tags[i]
                self.assertEqual(tag.key, tag_json.get('key'))
                self.assertEqual(tag.value, tag_json.get('value'))

    def _verify_json_match(self, serialized_json, original_json):
        # Check field by field to handle camelCase to snake_case conversion
        self.assertEqual(serialized_json.get('name'), original_json.get('name'))
        self.assertEqual(serialized_json.get('cron_expression'), original_json.get('cronExpression'))
        self.assertEqual(serialized_json.get('run_catchup_schedule_instances'),
                         original_json.get('runCatchupScheduleInstances'))
        self.assertEqual(serialized_json.get('paused'), original_json.get('paused'))
        self.assertEqual(serialized_json.get('schedule_start_time'), original_json.get('scheduleStartTime'))
        self.assertEqual(serialized_json.get('schedule_end_time'), original_json.get('scheduleEndTime'))
        self.assertEqual(serialized_json.get('create_time'), original_json.get('createTime'))
        self.assertEqual(serialized_json.get('updated_time'), original_json.get('updatedTime'))
        self.assertEqual(serialized_json.get('created_by'), original_json.get('createdBy'))
        self.assertEqual(serialized_json.get('updated_by'), original_json.get('updatedBy'))
        self.assertEqual(serialized_json.get('zone_id'), original_json.get('zoneId'))
        self.assertEqual(serialized_json.get('paused_reason'), original_json.get('pausedReason'))
        self.assertEqual(serialized_json.get('description'), original_json.get('description'))

        # Check StartWorkflowRequest
        if 'startWorkflowRequest' in original_json and original_json['startWorkflowRequest'] is not None:
            orig_req = original_json['startWorkflowRequest']
            serial_req = serialized_json.get('start_workflow_request')

            self.assertIsNotNone(serial_req)
            self.assertEqual(serial_req.get('name'), orig_req.get('name'))
            self.assertEqual(serial_req.get('version'), orig_req.get('version'))
            self.assertEqual(serial_req.get('correlation_id'), orig_req.get('correlationId'))
            self.assertEqual(serial_req.get('input'), orig_req.get('input'))

        # Check Tags
        if 'tags' in original_json and original_json['tags'] is not None:
            orig_tags = original_json['tags']
            serial_tags = serialized_json.get('tags')

            self.assertIsNotNone(serial_tags)
            self.assertEqual(len(serial_tags), len(orig_tags))

            for i, orig_tag in enumerate(orig_tags):
                serial_tag = serial_tags[i]
                self.assertEqual(serial_tag.get('key'), orig_tag.get('key'))
                self.assertEqual(serial_tag.get('value'), orig_tag.get('value'))


if __name__ == '__main__':
    unittest.main()