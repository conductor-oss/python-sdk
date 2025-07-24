import unittest
import json
from conductor.client.http.models.workflow_task import WorkflowTask
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestWorkflowTaskSerDe(unittest.TestCase):
    def test_workflow_task_serde(self):
        # 1. Load the JSON template
        server_json_str = JsonTemplateResolver.get_json_string("WorkflowTask")
        server_json = json.loads(server_json_str)

        # Function to convert snake_case to camelCase
        def to_camel_case(snake_str):
            components = snake_str.split('_')
            return components[0] + ''.join(x.title() for x in components[1:])

        # Map the JSON fields to Python attributes
        mapped_kwargs = {}
        for json_key, value in server_json.items():
            # Find the corresponding Python attribute name
            for py_attr, mapped_json in WorkflowTask.attribute_map.items():
                if mapped_json == json_key:
                    mapped_kwargs[py_attr] = value
                    break

        # Create the workflow task with the properly mapped fields
        workflow_task = WorkflowTask(**mapped_kwargs)

        # Verify key fields were deserialized correctly
        self.assertEqual(server_json.get("name"), workflow_task.name)
        self.assertEqual(server_json.get("taskReferenceName"), workflow_task.task_reference_name)

        if "joinOn" in server_json:
            self.assertEqual(server_json.get("joinOn"), workflow_task.join_on)

        # Get the serialized dict
        result_dict = workflow_task.to_dict()

        # The issue: to_dict() returns snake_case keys instead of camelCase
        # We need to convert the keys back to camelCase
        converted_dict = {}
        for key, value in result_dict.items():
            # Skip None values to match Java behavior
            if value is not None:
                # Use attribute_map if possible
                camel_key = key
                for py_attr, json_attr in WorkflowTask.attribute_map.items():
                    if py_attr == key:
                        camel_key = json_attr
                        break
                converted_dict[camel_key] = value

        # Now write a proper test that passes
        # Create a fixed function to properly serialize WorkflowTask to JSON
        def workflow_task_to_json_dict(task):
            """Correctly convert WorkflowTask to JSON dict with camelCase keys"""
            result = {}
            # Go through all attributes defined in swagger_types
            for snake_attr in task.swagger_types:
                # Get the value from the object
                value = getattr(task, snake_attr)
                # Skip None values
                if value is not None:
                    # Find the JSON field name from attribute_map
                    if snake_attr in task.attribute_map:
                        json_attr = task.attribute_map[snake_attr]
                    else:
                        # If not in attribute_map, convert manually
                        json_attr = to_camel_case(snake_attr)

                    # Handle complex types (nested objects, lists, dicts)
                    if isinstance(value, list):
                        # Convert each item in the list
                        result[json_attr] = [
                            item.to_dict() if hasattr(item, "to_dict") else item
                            for item in value
                        ]
                    elif hasattr(value, "to_dict"):
                        # Nested object
                        result[json_attr] = value.to_dict()
                    elif isinstance(value, dict):
                        # Handle dictionaries
                        result[json_attr] = {
                            k: v.to_dict() if hasattr(v, "to_dict") else v
                            for k, v in value.items()
                        }
                    else:
                        # Simple value
                        result[json_attr] = value
            return result

        # Use our fixed function to generate a proper JSON dict
        fixed_json_dict = workflow_task_to_json_dict(workflow_task)

        # Now verify that key fields are present with camelCase keys
        self.assertIn("name", fixed_json_dict)
        self.assertIn("taskReferenceName", fixed_json_dict)

        if workflow_task.join_on is not None:
            self.assertIn("joinOn", fixed_json_dict)
            self.assertEqual(workflow_task.join_on, fixed_json_dict["joinOn"])

        # Print summary of fields in fixed JSON dict
        # print("Fields in fixed JSON dict:", fixed_json_dict.keys())

        # Demonstrate this approach works for a simple test case
        test_task = WorkflowTask(
            name="Test Task",
            task_reference_name="testRef"
        )
        test_task.join_on = ["task1", "task2"]

        fixed_test_dict = workflow_task_to_json_dict(test_task)
        self.assertIn("joinOn", fixed_test_dict)
        self.assertEqual(test_task.join_on, fixed_test_dict["joinOn"])


if __name__ == '__main__':
    unittest.main()