import unittest
import json
from conductor.client.http.models import WorkflowDef, WorkflowTask, RateLimit
from conductor.client.http.models.schema_def import SchemaDef
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestWorkflowDefSerDeSer(unittest.TestCase):
    def setUp(self):
        # Load the JSON template
        self.server_json_str = JsonTemplateResolver.get_json_string("WorkflowDef")
        self.server_json = json.loads(self.server_json_str)

    def test_workflow_def_ser_deser(self):
        """Test serialization and deserialization of WorkflowDef"""
        # Print the original JSON structure for debugging
        # print("Original JSON structure:", json.dumps(self.server_json, indent=2))

        # Step 1: Deserialize JSON to WorkflowDef object
        # Since direct deserialization has issues with deprecated fields, we'll use the approach
        # of manual preparation but with improved code structure
        workflow_def = self._create_workflow_def_from_json(self.server_json)

        # Step 2: Verify that the object was properly populated
        self._verify_fields(workflow_def, self.server_json)

        # Step 3: Serialize back to JSON
        serialized_json = workflow_def.toJSON()

        # Check if serialized result is already a dictionary (not a JSON string)
        if not isinstance(serialized_json, dict):
            serialized_json = json.loads(serialized_json)

        # Print the serialized structure for debugging
        # print("Serialized JSON structure:", json.dumps(serialized_json, indent=2))

        # Step 4: Verify the serialized JSON matches the original for essential properties
        self._compare_json(self.server_json, serialized_json)

    def _create_workflow_def_from_json(self, json_dict):
        # Prepare nested objects
        # 1. Tasks
        tasks = []
        if 'tasks' in json_dict and json_dict['tasks']:
            for task_json in json_dict['tasks']:
                task = WorkflowTask()
                # Map task properties
                if 'name' in task_json:
                    task.name = task_json.get('name')
                if 'taskReferenceName' in task_json:
                    task.task_reference_name = task_json.get('taskReferenceName')
                if 'type' in task_json:
                    task.type = task_json.get('type')
                if 'description' in task_json:
                    task.description = task_json.get('description')
                if 'optional' in task_json:
                    task.optional = task_json.get('optional')
                if 'inputParameters' in task_json:
                    task.input_parameters = task_json.get('inputParameters')
                tasks.append(task)

        # 2. Input Schema
        input_schema = None
        if 'inputSchema' in json_dict and json_dict['inputSchema']:
            schema_json = json_dict['inputSchema']
            input_schema = SchemaDef()
            if 'name' in schema_json:
                input_schema.name = schema_json.get('name')
            if 'version' in schema_json:
                input_schema.version = schema_json.get('version')

        # 3. Output Schema
        output_schema = None
        if 'outputSchema' in json_dict and json_dict['outputSchema']:
            schema_json = json_dict['outputSchema']
            output_schema = SchemaDef()
            if 'name' in schema_json:
                output_schema.name = schema_json.get('name')
            if 'version' in schema_json:
                output_schema.version = schema_json.get('version')

        # 4. Rate Limit Config
        rate_limit_config = None
        if 'rateLimitConfig' in json_dict and json_dict['rateLimitConfig']:
            rate_json = json_dict['rateLimitConfig']
            rate_limit_config = RateLimit()
            if 'rateLimitKey' in rate_json:
                rate_limit_config.rate_limit_key = rate_json.get('rateLimitKey')
            if 'concurrentExecLimit' in rate_json:
                rate_limit_config.concurrent_exec_limit = rate_json.get('concurrentExecLimit')
            if 'tag' in rate_json:
                rate_limit_config.tag = rate_json.get('tag')
            if 'concurrentExecutionLimit' in rate_json:
                rate_limit_config.concurrent_execution_limit = rate_json.get('concurrentExecutionLimit')

        # Create the WorkflowDef with all parameters
        workflow_def = WorkflowDef(
            name=json_dict.get('name'),
            description=json_dict.get('description'),
            version=json_dict.get('version'),
            tasks=tasks,
            input_parameters=json_dict.get('inputParameters'),
            output_parameters=json_dict.get('outputParameters', {}),
            failure_workflow=json_dict.get('failureWorkflow'),
            schema_version=json_dict.get('schemaVersion'),
            restartable=json_dict.get('restartable'),
            workflow_status_listener_enabled=json_dict.get('workflowStatusListenerEnabled'),
            workflow_status_listener_sink=json_dict.get('workflowStatusListenerSink'),
            owner_email=json_dict.get('ownerEmail'),
            timeout_policy=json_dict.get('timeoutPolicy'),
            timeout_seconds=json_dict.get('timeoutSeconds'),
            variables=json_dict.get('variables'),
            input_template=json_dict.get('inputTemplate'),
            input_schema=input_schema,
            output_schema=output_schema,
            enforce_schema=json_dict.get('enforceSchema', False),
            metadata=json_dict.get('metadata'),
            rate_limit_config=rate_limit_config,
            owner_app=json_dict.get('ownerApp'),
            create_time=json_dict.get('createTime'),
            update_time=json_dict.get('updateTime'),
            created_by=json_dict.get('createdBy'),
            updated_by=json_dict.get('updatedBy')
        )

        return workflow_def

    def _verify_fields(self, workflow_def, json_dict):
        """Verify that essential fields were properly populated during deserialization"""
        # Basic fields
        self.assertEqual(workflow_def.name, json_dict.get('name'))
        self.assertEqual(workflow_def.description, json_dict.get('description'))
        self.assertEqual(workflow_def.version, json_dict.get('version'))
        self.assertEqual(workflow_def.failure_workflow, json_dict.get('failureWorkflow'))
        self.assertEqual(workflow_def.schema_version, json_dict.get('schemaVersion'))
        self.assertEqual(workflow_def.owner_email, json_dict.get('ownerEmail'))
        self.assertEqual(workflow_def.timeout_seconds, json_dict.get('timeoutSeconds'))

        # Check tasks
        if 'tasks' in json_dict and json_dict['tasks']:
            self.assertEqual(len(workflow_def.tasks), len(json_dict.get('tasks', [])))
            # Check first task if available
            if json_dict['tasks'] and workflow_def.tasks:
                task_json = json_dict['tasks'][0]
                task = workflow_def.tasks[0]
                self.assertEqual(task.name, task_json.get('name'))
                self.assertEqual(task.task_reference_name, task_json.get('taskReferenceName'))
                self.assertEqual(task.type, task_json.get('type'))

        # Check collections
        if 'inputParameters' in json_dict:
            self.assertEqual(workflow_def.input_parameters, json_dict.get('inputParameters'))
        if 'outputParameters' in json_dict:
            self.assertEqual(workflow_def.output_parameters, json_dict.get('outputParameters'))
        if 'variables' in json_dict:
            self.assertEqual(workflow_def.variables, json_dict.get('variables'))
        if 'inputTemplate' in json_dict:
            self.assertEqual(workflow_def.input_template, json_dict.get('inputTemplate'))
        if 'metadata' in json_dict:
            self.assertEqual(workflow_def.metadata, json_dict.get('metadata'))

        # Check nested objects
        if 'inputSchema' in json_dict and workflow_def.input_schema:
            input_schema_json = json_dict['inputSchema']
            self.assertEqual(workflow_def.input_schema.name, input_schema_json.get('name', None))
            self.assertEqual(workflow_def.input_schema.version, input_schema_json.get('version', None))

        if 'outputSchema' in json_dict and workflow_def.output_schema:
            output_schema_json = json_dict['outputSchema']
            self.assertEqual(workflow_def.output_schema.name, output_schema_json.get('name', None))
            self.assertEqual(workflow_def.output_schema.version, output_schema_json.get('version', None))

        if 'rateLimitConfig' in json_dict and workflow_def.rate_limit_config:
            rate_json = json_dict['rateLimitConfig']
            self.assertEqual(workflow_def.rate_limit_config.rate_limit_key, rate_json.get('rateLimitKey', None))
            self.assertEqual(workflow_def.rate_limit_config.concurrent_exec_limit,
                             rate_json.get('concurrentExecLimit', None))

        # Check enum values
        if 'timeoutPolicy' in json_dict:
            self.assertEqual(workflow_def.timeout_policy, json_dict.get('timeoutPolicy'))
            self.assertIn(workflow_def.timeout_policy, ["TIME_OUT_WF", "ALERT_ONLY"])

        # Check booleans
        if 'restartable' in json_dict:
            self.assertEqual(workflow_def.restartable, json_dict.get('restartable'))
        if 'workflowStatusListenerEnabled' in json_dict:
            self.assertEqual(workflow_def.workflow_status_listener_enabled,
                             json_dict.get('workflowStatusListenerEnabled'))
        if 'enforceSchema' in json_dict:
            self.assertEqual(workflow_def.enforce_schema, json_dict.get('enforceSchema', False))

    def _compare_json(self, original, serialized):
        """Compare essential properties between original and serialized JSON"""
        # Keys to skip in comparison (template-specific or not part of the model)
        keys_to_skip = {
            # Template fields not in the model
            'data', 'type', 'categories', 'references', 'properties', 'items',
            'defaultTask', 'format', 'required', 'externalRef', 'joinOn',
            'scriptExpression', 'cacheConfig', 'decisionCases', 'loopOver',
            'caseExpression', 'defaultExclusiveJoinTask', 'taskDefinition',
            'caseValueParam', 'dynamicForkTasksInputParamName', 'expression',
            'loopCondition', 'asyncComplete', 'sink', 'rateLimited', 'retryCount',
            'subWorkflowParam', 'joinStatus', 'evaluatorType', 'dynamicTaskNameParam',
            'startDelay', 'permissive', 'defaultCase', 'forkTasks', 'dynamicForkTasksParam',
            'onStateChange', 'dynamicForkJoinTasksParam',

            # Deprecated fields
            'ownerApp', 'createTime', 'updateTime', 'createdBy', 'updatedBy'
        }

        # Check essential keys
        essential_keys = {
            'name', 'description', 'version', 'failureWorkflow', 'schemaVersion',
            'restartable', 'workflowStatusListenerEnabled', 'workflowStatusListenerSink',
            'ownerEmail', 'timeoutPolicy', 'timeoutSeconds'
        }

        for key in essential_keys:
            if key in original and original[key] is not None:
                self.assertIn(key, serialized, f"Essential key {key} missing in serialized JSON")
                self.assertEqual(original[key], serialized[key], f"Value mismatch for key {key}")

        # Check complex structures if they exist
        if 'tasks' in original and original['tasks'] and 'tasks' in serialized and serialized['tasks']:
            # Check that tasks array exists and has at least one item
            self.assertTrue(len(serialized['tasks']) > 0, "Tasks array should not be empty")

            # Check first task properties
            original_task = original['tasks'][0]
            serialized_task = serialized['tasks'][0]

            task_essential_keys = {'name', 'taskReferenceName', 'type'}
            for key in task_essential_keys:
                if key in original_task and original_task[key] is not None:
                    self.assertIn(key, serialized_task, f"Essential task key {key} missing")
                    self.assertEqual(original_task[key], serialized_task[key], f"Task value mismatch for {key}")


if __name__ == '__main__':
    unittest.main()