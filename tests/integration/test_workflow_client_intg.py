import logging
import os
import unittest

from tests.integration.client.orkes.test_orkes_clients import TestOrkesClients
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from tests.integration.metadata.test_workflow_definition import run_workflow_definition_tests
from tests.integration.workflow.test_workflow_execution import run_workflow_execution_tests

WORKFLOW_NAME = 'ut_wf'
WORKFLOW_UUID = 'ut_wf_uuid'
TASK_NAME = 'ut_task'
CORRELATION_ID = 'correlation_id'

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)


def get_configuration():
    configuration = Configuration()
    configuration.debug = False
    configuration.apply_logging_config()
    return configuration


class TestOrkesWorkflowClientIntg(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = get_configuration()
        cls.workflow_client = OrkesWorkflowClient(cls.config)
        logger.info(f'setting up TestOrkesWorkflowClientIntg with config {cls.config}')

    def test_all(self):
        logger.info('START: integration tests')
        configuration = self.config
        workflow_executor = WorkflowExecutor(configuration)

        # test_async.test_async_method(api_client)
        run_workflow_definition_tests(workflow_executor)
        run_workflow_execution_tests(configuration, workflow_executor)
        TestOrkesClients(configuration=configuration).run()
        logger.info('END: integration tests')
