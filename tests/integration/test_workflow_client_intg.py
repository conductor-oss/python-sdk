import logging
import os
import time
import unittest

import pytest

from tests.integration.client.orkes.test_orkes_clients import TestOrkesClients
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from tests.integration.metadata.test_workflow_definition import run_workflow_definition_tests
from tests.integration.workflow.test_workflow_execution import run_workflow_execution_tests
from tests.integration.retry_helpers import DEFAULT_OVERALL_DEADLINE_SECONDS

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
        from tests.integration.conftest import skip_if_server_unavailable
        skip_if_server_unavailable()

        cls.config = get_configuration()
        cls.workflow_client = OrkesWorkflowClient(cls.config)
        logger.info(f'setting up TestOrkesWorkflowClientIntg with config {cls.config}')

    @pytest.mark.slow_test_all
    def test_all(self):
        logger.info('START: integration tests')
        configuration = self.config
        workflow_executor = WorkflowExecutor(configuration)

        # One shared wall-clock budget for the whole aggregate suite. Each
        # sub-suite runs its scenarios once; a scenario that hits a transient
        # (status 0) transport blip against the shared dev server retries until
        # this deadline passes, with capped exponential backoff (see
        # tests/integration/retry_helpers.py). Real failures raise immediately.
        deadline = time.monotonic() + DEFAULT_OVERALL_DEADLINE_SECONDS

        run_workflow_definition_tests(workflow_executor, deadline=deadline)
        run_workflow_execution_tests(configuration, workflow_executor, deadline=deadline)
        TestOrkesClients(configuration=configuration).run(deadline=deadline)
        logger.info('END: integration tests')
