import unittest
import json
from conductor.client.http.models import Workflow, Task, WorkflowDef
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class WorkflowSerDeserTest(unittest.TestCase):
    def setUp(self):
        self.server_json_str = JsonTemplateResolver.get_json_string("Workflow")
        self.server_json = json.loads(self.server_json_str)

    def test_workflow_serde(self):
        # 1. Create a complete workflow object from JSON
        workflow = self._create_workflow_from_json(self.server_json)

        # 2. Verify all fields are properly populated
        self._verify_workflow_fields(workflow, self.server_json)

        # 3. Serialize back to JSON
        result_json = workflow.to_dict()

        # 4. Compare original and resulting JSON
        self._compare_json_objects(self.server_json, result_json)

    def _create_workflow_from_json(self, json_data):
        """Create a Workflow object with all fields from JSON"""
        # Handle tasks if present
        tasks = None
        if json_data.get("tasks"):
            tasks = [self._create_task_from_json(task_json) for task_json in json_data.get("tasks")]

        # Handle workflow definition if present
        workflow_def = None
        if json_data.get("workflowDefinition"):
            workflow_def = self._create_workflow_def_from_json(json_data.get("workflowDefinition"))

        # Handle sets
        failed_ref_tasks = set(json_data.get("failedReferenceTaskNames", []))
        failed_tasks = set(json_data.get("failedTaskNames", []))

        # Handle history if present
        history = None
        if json_data.get("history"):
            history = [self._create_workflow_from_json(wf_json) for wf_json in json_data.get("history")]

        # Create the workflow with all fields
        return Workflow(
            owner_app=json_data.get("ownerApp"),
            create_time=json_data.get("createTime"),
            update_time=json_data.get("updateTime"),
            created_by=json_data.get("createdBy"),
            updated_by=json_data.get("updatedBy"),
            status=json_data.get("status"),
            end_time=json_data.get("endTime"),
            workflow_id=json_data.get("workflowId"),
            parent_workflow_id=json_data.get("parentWorkflowId"),
            parent_workflow_task_id=json_data.get("parentWorkflowTaskId"),
            tasks=tasks,
            input=json_data.get("input"),
            output=json_data.get("output"),
            correlation_id=json_data.get("correlationId"),
            re_run_from_workflow_id=json_data.get("reRunFromWorkflowId"),
            reason_for_incompletion=json_data.get("reasonForIncompletion"),
            event=json_data.get("event"),
            task_to_domain=json_data.get("taskToDomain"),
            failed_reference_task_names=failed_ref_tasks,
            workflow_definition=workflow_def,
            external_input_payload_storage_path=json_data.get("externalInputPayloadStoragePath"),
            external_output_payload_storage_path=json_data.get("externalOutputPayloadStoragePath"),
            priority=json_data.get("priority"),
            variables=json_data.get("variables"),
            last_retried_time=json_data.get("lastRetriedTime"),
            failed_task_names=failed_tasks,
            history=history,
            idempotency_key=json_data.get("idempotencyKey"),
            rate_limit_key=json_data.get("rateLimitKey"),
            rate_limited=json_data.get("rateLimited"),
            start_time=json_data.get("startTime"),
            workflow_name=json_data.get("workflowName"),
            workflow_version=json_data.get("workflowVersion")
        )

    def _create_task_from_json(self, task_json):
        """Create a Task object from JSON"""
        # Create a Task object with fields from task_json
        task = Task()

        # Access all possible fields from task_json and set them on the task object
        for py_field, json_field in Task.attribute_map.items():
            if json_field in task_json:
                setattr(task, py_field, task_json.get(json_field))

        return task

    def _create_workflow_def_from_json(self, workflow_def_json):
        """Create a WorkflowDef object from JSON"""
        # Create a WorkflowDef object with fields from workflow_def_json
        workflow_def = WorkflowDef()

        # Access all possible fields from workflow_def_json and set them on the workflow_def object
        for py_field, json_field in WorkflowDef.attribute_map.items():
            if json_field in workflow_def_json:
                # Special handling for nested objects or complex types could be added here
                setattr(workflow_def, py_field, workflow_def_json.get(json_field))

        return workflow_def

    def _verify_workflow_fields(self, workflow, json_data):
        """Verify that all fields in the Workflow object match the JSON data"""
        # Check all fields defined in the model
        for py_field, json_field in Workflow.attribute_map.items():
            if json_field in json_data:
                python_value = getattr(workflow, py_field)
                json_value = json_data.get(json_field)

                # Skip complex objects that need special handling
                if py_field in ['tasks', 'workflow_definition', 'history']:
                    continue

                # Handle sets which need conversion
                if py_field in ['failed_reference_task_names', 'failed_task_names'] and json_value:
                    self.assertEqual(set(python_value), set(json_value))
                    continue

                # Handle dictionaries and other simple types
                self.assertEqual(python_value, json_value, f"Field {py_field} doesn't match")

    def _compare_json_objects(self, original, result):
        """Compare original and resulting JSON objects"""
        # For each field in the original JSON
        for key in original:
            if key in result:
                # Handle sets vs lists conversion for known set fields
                if key in ["failedReferenceTaskNames", "failedTaskNames"]:
                    if isinstance(original[key], list) and isinstance(result[key], (list, set)):
                        self.assertEqual(set(original[key]), set(result[key]),
                                         f"Field {key} doesn't match after set conversion")
                    continue

                # If it's a nested object
                if isinstance(original[key], dict) and isinstance(result[key], dict):
                    self._compare_json_objects(original[key], result[key])
                # If it's a list
                elif isinstance(original[key], list) and isinstance(result[key], list):
                    self.assertEqual(len(original[key]), len(result[key]))
                    # For complex objects in lists, we could add recursive comparison
                # Simple value
                else:
                    self.assertEqual(original[key], result[key], f"Field {key} doesn't match")
            else:
                # Check if there's a field mapping issue
                snake_key = self._camel_to_snake(key)
                if snake_key in result:
                    # Handle sets vs lists for known set fields
                    if key in ["failedReferenceTaskNames", "failedTaskNames"]:
                        if isinstance(original[key], list) and isinstance(result[snake_key], (list, set)):
                            self.assertEqual(set(original[key]), set(result[snake_key]),
                                             f"Field {key} doesn't match after set conversion")
                        continue

                    # Compare with the snake_case key
                    if isinstance(original[key], dict) and isinstance(result[snake_key], dict):
                        self._compare_json_objects(original[key], result[snake_key])
                    elif isinstance(original[key], list) and isinstance(result[snake_key], list):
                        self.assertEqual(len(original[key]), len(result[snake_key]))
                    else:
                        self.assertEqual(original[key], result[snake_key], f"Field {key} doesn't match")
                else:
                    # Check if the attribute is defined in swagger_types but has a different JSON name
                    for py_field, json_field in Workflow.attribute_map.items():
                        if json_field == key and py_field in result:
                            if key in ["failedReferenceTaskNames", "failedTaskNames"]:
                                if isinstance(original[key], list) and isinstance(result[py_field], (list, set)):
                                    self.assertEqual(set(original[key]), set(result[py_field]),
                                                     f"Field {key} doesn't match after set conversion")
                                break

                            if isinstance(original[key], dict) and isinstance(result[py_field], dict):
                                self._compare_json_objects(original[key], result[py_field])
                            elif isinstance(original[key], list) and isinstance(result[py_field], list):
                                self.assertEqual(len(original[key]), len(result[py_field]))
                            else:
                                self.assertEqual(original[key], result[py_field], f"Field {key} doesn't match")
                            break
                    else:
                        # If the field isn't in result and we can't find a mapping,
                        # it might be a field that isn't defined in the model
                        self.fail(f"Field {key} is missing in the result")

    def _camel_to_snake(self, name):
        """Convert camelCase to snake_case"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


if __name__ == '__main__':
    unittest.main()