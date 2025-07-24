import unittest
from conductor.client.http.models.action import Action
from conductor.client.http.models.start_workflow import StartWorkflow
from conductor.client.http.models.task_details import TaskDetails
from conductor.client.http.models.terminate_workflow import TerminateWorkflow
from conductor.client.http.models.update_workflow_variables import UpdateWorkflowVariables
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver
import json
import re


class TestActionSerDes(unittest.TestCase):
    def setUp(self):
        # Load the JSON template
        self.server_json_str = JsonTemplateResolver.get_json_string("EventHandler.Action")
        self.server_json = json.loads(self.server_json_str)

    def _camel_to_snake(self, name):
        """Convert camelCase to snake_case"""
        # Insert underscore before uppercase letters and convert to lowercase
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _create_model_object(self, model_class, json_data):
        """Generic method to create model objects with proper camelCase to snake_case conversion"""
        if not json_data:
            return None

        # Create an instance of the model class
        obj = model_class()

        # Iterate through the JSON data and set attributes on the model object
        for key, value in json_data.items():
            # Convert camelCase to snake_case
            snake_key = self._camel_to_snake(key)

            # Try to set the attribute if it exists on the model
            if hasattr(obj, snake_key):
                setattr(obj, snake_key, value)

        return obj

    def test_action_serdes(self):
        # 1. Test deserialization of server JSON to SDK model
        action_obj = Action(
            action=self.server_json.get("action"),
            start_workflow=self._create_model_object(StartWorkflow, self.server_json.get("start_workflow")),
            complete_task=self._create_model_object(TaskDetails, self.server_json.get("complete_task")),
            fail_task=self._create_model_object(TaskDetails, self.server_json.get("fail_task")),
            expand_inline_json=self.server_json.get("expandInlineJSON"),
            terminate_workflow=self._create_model_object(TerminateWorkflow, self.server_json.get("terminate_workflow")),
            update_workflow_variables=self._create_model_object(UpdateWorkflowVariables,
                                                                self.server_json.get("update_workflow_variables"))
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(self.server_json.get("action"), action_obj.action)

        # Check if start_workflow exists in the JSON
        if "start_workflow" in self.server_json:
            self.assertIsNotNone(action_obj.start_workflow)

        # Check if complete_task exists in the JSON
        if "complete_task" in self.server_json:
            self.assertIsNotNone(action_obj.complete_task)

        # Check if fail_task exists in the JSON
        if "fail_task" in self.server_json:
            self.assertIsNotNone(action_obj.fail_task)

        # Check if expandInlineJSON exists in the JSON
        if "expandInlineJSON" in self.server_json:
            self.assertEqual(self.server_json.get("expandInlineJSON"), action_obj.expand_inline_json)

        # Check if terminate_workflow exists in the JSON
        if "terminate_workflow" in self.server_json:
            self.assertIsNotNone(action_obj.terminate_workflow)

        # Check if update_workflow_variables exists in the JSON
        if "update_workflow_variables" in self.server_json:
            self.assertIsNotNone(action_obj.update_workflow_variables)

        # 3. Verify the action enum value is valid
        allowed_values = ["start_workflow", "complete_task", "fail_task", "terminate_workflow",
                          "update_workflow_variables"]
        self.assertIn(action_obj.action, allowed_values)

        # 4. Test serialization back to JSON
        result_json = action_obj.to_dict()

        # 5. Verify the result JSON has the same keys and values as the original
        for key in self.server_json:
            if key == "expandInlineJSON":
                # Handle camelCase to snake_case conversion
                self.assertEqual(self.server_json[key], result_json["expand_inline_json"])
            elif key in ["terminate_workflow", "start_workflow", "complete_task", "fail_task",
                         "update_workflow_variables"]:
                # For nested objects, verify they exist in result_json
                if self.server_json[key] is not None:
                    self.assertIsNotNone(result_json[key])

                    # For terminate_workflow, check specific camelCase fields
                    if key == "terminate_workflow" and key in result_json:
                        term_json = self.server_json[key]
                        result_term = result_json[key]

                        # Maps the expected field names from server JSON to the result JSON
                        if "workflowId" in term_json and "workflowId" in result_term:
                            self.assertEqual(term_json["workflowId"], result_term["workflowId"])
                        if "terminationReason" in term_json and "terminationReason" in result_term:
                            self.assertEqual(term_json["terminationReason"], result_term["terminationReason"])

                    # For update_workflow_variables, check specific camelCase fields
                    if key == "update_workflow_variables" and key in result_json:
                        update_json = self.server_json[key]
                        result_update = result_json[key]

                        # Maps the expected field names from server JSON to the result JSON
                        if "workflowId" in update_json and "workflowId" in result_update:
                            self.assertEqual(update_json["workflowId"], result_update["workflowId"])
                        if "variables" in update_json and "variables" in result_update:
                            self.assertEqual(update_json["variables"], result_update["variables"])
                        if "appendArray" in update_json and "appendArray" in result_update:
                            self.assertEqual(update_json["appendArray"], result_update["appendArray"])
            elif key in result_json:
                # Direct comparison for keys that match
                self.assertEqual(self.server_json[key], result_json[key])


if __name__ == '__main__':
    unittest.main()