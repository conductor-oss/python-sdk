import logging
import unittest
from conductor.client.configuration.configuration import Configuration
from conductor.client.adapters.models import TaskDef, WorkflowDef, WorkflowTask
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient

TASK_NAME = 'task-test-sdk'
WORKFLOW_NAME = 'sdk-workflow-test-0'

schema = {
    "name": "schema-test-sdk",
    "type": "JSON",
    "data": {
        "type": "object",
        "properties": {
            "$schema": "http://json-schema.org/draft-07/schema"
        }
    }
}
task = {
    "name": TASK_NAME,
    "description": "",
    "retry_count": 3,
    "timeout_seconds": 3600,
    "timeout_policy": "TIME_OUT_WF",
    "retry_logic": "FIXED",
    "retry_delay_seconds": 60,
    "response_timeout_seconds": 600,
    "rate_limit_per_frequency": 0,
    "rate_limit_frequency_in_seconds": 1,
    "owner_email": "viren@orkes.io",
    "poll_timeout_seconds": 3600,
    "input_keys": [],
    "output_keys": [],
    "input_template": {},
    "backoff_scale_factor": 1,
    "concurrent_exec_limit": 0,
    "input_schema": schema,
    "output_schema": schema,
    "enforce_schema": True
}


workflow = {
    "name": WORKFLOW_NAME,
    "description": "",
    "version": 1,
    "tasks": [
        {
            "name": "simple",
            "taskReferenceName": "simple_ref",
            "type": "SIMPLE",
            "taskDefinition": {
                "inputSchema": schema,
                "outputSchema": schema,
                "enforce_schema": True
            }
        }
    ],
    "input_parameters": [],
    "output_parameters": {},
    "schema_version": 2,
    "restartable": True,
    "workflow_status_listener_enabled": False,
    "owner_email": "viren@orkes.io",
    "timeout_policy": "ALERT_ONLY",
    "timeout_seconds": 0,
    "failure_workflow": "",
    "input_schema": schema,
    "output_schema": schema,
    "enforce_schema": True
}



class TestOrkesMetadataClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        configuration = Configuration()
        cls.metadata_client = OrkesMetadataClient(configuration)

    def setUp(self):
        self.taskDef = TaskDef(name='task-test-sdk-0')
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_register_task(self):
        self.metadata_client.register_task_def(task_def=TaskDef(**task))
        response = self.metadata_client.get_task_def(task_type=TASK_NAME)
        self.assertEqual(response.name, TASK_NAME)
        self.assertEqual(response.input_schema.name, schema['name'])
        self.assertEqual(response.output_schema.type, schema['type'])
        self.assertEqual(response.enforce_schema, True)

        no_schema_task = TaskDef(name='task-sdk-no-schema')
        self.metadata_client.register_task_def(task_def=no_schema_task)
        response = self.metadata_client.get_task_def(task_type=no_schema_task.name)
        self.assertEqual(response.name, no_schema_task.name)
        self.assertEqual(response.input_schema, None)
        self.assertEqual(response.output_schema, None)
        self.assertEqual(response.enforce_schema, False)

    def test_register_workflow_def(self):
        workflow_def = WorkflowDef(**workflow)

        self.metadata_client.register_workflow_def(workflow_def=workflow_def)
        response = self.metadata_client.get_workflow_def(name=WORKFLOW_NAME)
        self.assertEqual(response.name, WORKFLOW_NAME)
        self.assertEqual(response.input_schema.name, schema['name'])
        self.assertEqual(response.output_schema.type, schema['type'])
        self.assertEqual(response.enforce_schema, True)

        no_schema_wf = WorkflowDef(name='workflow-sdk-no-schema', tasks=[
            WorkflowTask(name='test', task_reference_name='test_ref', task_definition=TaskDef())])
        self.metadata_client.register_workflow_def(workflow_def=no_schema_wf)
        response = self.metadata_client.get_workflow_def(name=no_schema_wf.name)
        self.assertEqual(response.name, no_schema_wf.name)
        self.assertEqual(len(response.tasks), 1)
        self.assertEqual(response.tasks[0].task_definition.output_schema, None)
        self.assertEqual(response.tasks[0].task_definition.input_schema, None)
        self.assertEqual(response.tasks[0].task_definition.enforce_schema, False)

        no_schema_wf = WorkflowDef(name='workflow-sdk-no-schema', tasks=[
            WorkflowTask(name='test', task_reference_name='test_ref')])
        self.metadata_client.register_workflow_def(workflow_def=no_schema_wf)
        response = self.metadata_client.get_workflow_def(name=no_schema_wf.name)
        self.assertEqual(response.name, no_schema_wf.name)
        self.assertEqual(len(response.tasks), 1)
        self.assertEqual(response.tasks[0].task_definition, None)



if __name__ == '__main__':
    unittest.main()
