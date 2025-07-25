import unittest
import json
from conductor.client.http.models.workflow_test_request import WorkflowTestRequest, TaskMock
from conductor.client.http.models.workflow_def import WorkflowDef
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestWorkflowTestRequestSerDes(unittest.TestCase):
    """Unit test for WorkflowTestRequest serialization and deserialization"""

    def setUp(self):
        # Load JSON template from JsonTemplateResolver
        self.server_json_str = JsonTemplateResolver.get_json_string("WorkflowTestRequest")
        self.server_json = json.loads(self.server_json_str)

    def snake_to_camel(self, snake_case):
        """Convert snake_case to camelCase"""
        components = snake_case.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    def test_workflow_test_request_serdes(self):
        """Test serialization and deserialization of WorkflowTestRequest"""

        # 1. Deserialize JSON into SDK model object
        workflow_test_request = WorkflowTestRequest(
            correlation_id=self.server_json.get("correlationId"),
            created_by=self.server_json.get("createdBy"),
            external_input_payload_storage_path=self.server_json.get("externalInputPayloadStoragePath"),
            input=self.server_json.get("input"),
            name=self.server_json.get("name"),
            priority=self.server_json.get("priority"),
            version=self.server_json.get("version")
        )

        # Handle complex nested structures
        if "taskToDomain" in self.server_json:
            workflow_test_request.task_to_domain = self.server_json.get("taskToDomain")

        # Handle workflowDef object if present
        if "workflowDef" in self.server_json and self.server_json["workflowDef"] is not None:
            workflow_def = WorkflowDef()
            # Assuming there are fields in WorkflowDef that need to be populated
            workflow_test_request.workflow_def = workflow_def

        # Handle subWorkflowTestRequest if present
        if "subWorkflowTestRequest" in self.server_json and self.server_json["subWorkflowTestRequest"]:
            sub_workflow_dict = {}
            for key, value in self.server_json["subWorkflowTestRequest"].items():
                # Create a sub-request for each entry
                sub_request = WorkflowTestRequest(name=value.get("name"))
                sub_workflow_dict[key] = sub_request
            workflow_test_request.sub_workflow_test_request = sub_workflow_dict

        # Handle taskRefToMockOutput if present
        if "taskRefToMockOutput" in self.server_json and self.server_json["taskRefToMockOutput"]:
            task_mock_dict = {}
            for task_ref, mock_list in self.server_json["taskRefToMockOutput"].items():
                task_mocks = []
                for mock_data in mock_list:
                    task_mock = TaskMock(
                        status=mock_data.get("status", "COMPLETED"),
                        output=mock_data.get("output"),
                        execution_time=mock_data.get("executionTime", 0),
                        queue_wait_time=mock_data.get("queueWaitTime", 0)
                    )
                    task_mocks.append(task_mock)
                task_mock_dict[task_ref] = task_mocks
            workflow_test_request.task_ref_to_mock_output = task_mock_dict

        # 2. Verify all fields are properly populated
        self.assertEqual(self.server_json.get("correlationId"), workflow_test_request.correlation_id)
        self.assertEqual(self.server_json.get("createdBy"), workflow_test_request.created_by)
        self.assertEqual(self.server_json.get("name"), workflow_test_request.name)
        self.assertEqual(self.server_json.get("priority"), workflow_test_request.priority)
        self.assertEqual(self.server_json.get("version"), workflow_test_request.version)

        # Verify complex nested structures if present
        if "taskToDomain" in self.server_json:
            self.assertEqual(self.server_json.get("taskToDomain"), workflow_test_request.task_to_domain)

        if "subWorkflowTestRequest" in self.server_json and self.server_json["subWorkflowTestRequest"]:
            self.assertIsNotNone(workflow_test_request.sub_workflow_test_request)
            for key in self.server_json["subWorkflowTestRequest"]:
                self.assertIn(key, workflow_test_request.sub_workflow_test_request)
                self.assertEqual(
                    self.server_json["subWorkflowTestRequest"][key].get("name"),
                    workflow_test_request.sub_workflow_test_request[key].name
                )

        if "taskRefToMockOutput" in self.server_json and self.server_json["taskRefToMockOutput"]:
            self.assertIsNotNone(workflow_test_request.task_ref_to_mock_output)
            for task_ref in self.server_json["taskRefToMockOutput"]:
                self.assertIn(task_ref, workflow_test_request.task_ref_to_mock_output)
                for i, mock_data in enumerate(self.server_json["taskRefToMockOutput"][task_ref]):
                    self.assertEqual(
                        mock_data.get("status", "COMPLETED"),
                        workflow_test_request.task_ref_to_mock_output[task_ref][i].status
                    )
                    self.assertEqual(
                        mock_data.get("output"),
                        workflow_test_request.task_ref_to_mock_output[task_ref][i].output
                    )

        # 3. Serialize model back to JSON
        model_dict = workflow_test_request.to_dict()

        # Convert snake_case keys to camelCase for comparison with original JSON
        serialized_json = {}
        for key, value in model_dict.items():
            camel_key = self.snake_to_camel(key)
            serialized_json[camel_key] = value

        # 4. Verify the serialized JSON matches the original
        # Check basic fields match (allowing for null/None differences)
        if "correlationId" in self.server_json:
            self.assertEqual(self.server_json["correlationId"], serialized_json["correlationId"])
        if "createdBy" in self.server_json:
            self.assertEqual(self.server_json["createdBy"], serialized_json["createdBy"])
        if "name" in self.server_json:
            self.assertEqual(self.server_json["name"], serialized_json["name"])
        if "priority" in self.server_json:
            self.assertEqual(self.server_json["priority"], serialized_json["priority"])
        if "version" in self.server_json:
            self.assertEqual(self.server_json["version"], serialized_json["version"])

        # Check maps and complex structures
        if "taskToDomain" in self.server_json:
            self.assertEqual(self.server_json["taskToDomain"], serialized_json["taskToDomain"])

        # Verify that sub-workflow structure is preserved correctly
        if "subWorkflowTestRequest" in self.server_json and self.server_json["subWorkflowTestRequest"]:
            self.assertIn("subWorkflowTestRequest", serialized_json)
            for key in self.server_json["subWorkflowTestRequest"]:
                self.assertIn(key, serialized_json["subWorkflowTestRequest"])
                orig_name = self.server_json["subWorkflowTestRequest"][key].get("name")
                serial_obj = serialized_json["subWorkflowTestRequest"][key]

                # Handle the case where to_dict() might return a dictionary or an object
                if isinstance(serial_obj, dict):
                    serial_name = serial_obj.get("name")
                else:
                    # Assuming it's an object with attribute access
                    serial_name = getattr(serial_obj, "name", None)

                self.assertEqual(orig_name, serial_name)

        # Verify task mock outputs
        if "taskRefToMockOutput" in self.server_json and self.server_json["taskRefToMockOutput"]:
            self.assertIn("taskRefToMockOutput", serialized_json)
            for task_ref in self.server_json["taskRefToMockOutput"]:
                self.assertIn(task_ref, serialized_json["taskRefToMockOutput"])
                for i, mock_data in enumerate(self.server_json["taskRefToMockOutput"][task_ref]):
                    orig_status = mock_data.get("status", "COMPLETED")
                    orig_output = mock_data.get("output")

                    serial_mock = serialized_json["taskRefToMockOutput"][task_ref][i]

                    # Handle the case where to_dict() might return a dictionary or an object
                    if isinstance(serial_mock, dict):
                        serial_status = serial_mock.get("status")
                        serial_output = serial_mock.get("output")
                    else:
                        # Assuming it's an object with attribute access
                        serial_status = getattr(serial_mock, "status", None)
                        serial_output = getattr(serial_mock, "output", None)

                    self.assertEqual(orig_status, serial_status)
                    self.assertEqual(orig_output, serial_output)


if __name__ == "__main__":
    unittest.main()