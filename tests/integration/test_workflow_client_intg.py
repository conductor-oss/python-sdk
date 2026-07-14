import logging
import os
import time
import unittest

import pytest

from tests.integration.client.orkes.test_orkes_clients import TestOrkesClients
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.http.rest import ApiException
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


def _first_transient_api_exception(exc):
    """Walk the exception chain (cause/context) and return the first transient
    ApiException (status 0 / flagged transient), if any.

    Inner test helpers sometimes catch an ApiException and re-raise it as a bare
    ``Exception`` (losing the type), so we can't rely on the outermost exception
    type alone. Implicit chaining still records the original on ``__context__``
    (or ``__cause__`` when ``raise ... from`` is used), so we follow that chain.
    """
    seen = set()
    cur = exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        if isinstance(cur, ApiException) and (
                getattr(cur, 'transient', False) or cur.status in (0, None)):
            return cur
        cur = cur.__cause__ or cur.__context__
    return None


def _run_tolerating_transient(label, func, *args, retries=3, **kwargs):
    """Run a sub-suite, retrying only on a transient (status 0) transport blip
    against the shared dev server.

    A `(0)` ApiException is a raw connection/protocol hiccup (read timeout,
    stale keep-alive, HTTP/2 GOAWAY race, client closed by a fork cleanup, etc.)
    — not a real assertion or server failure — and was observed flaking the
    `test-all` bucket. Retrying absorbs that network noise while still surfacing
    genuine failures immediately (any non-transient error, or a transient one on
    the final attempt, re-raises). We inspect the whole exception chain because
    sub-suites may wrap the ApiException in a generic Exception.
    """
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            transient = _first_transient_api_exception(e)
            if transient is not None and attempt < retries - 1:
                logger.warning(
                    'transient (%s) API error in %s (attempt %d/%d): %s; retrying',
                    transient.status, label, attempt + 1, retries, transient)
                time.sleep(2 ** attempt)
                continue
            raise


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

        # test_async.test_async_method(api_client)
        _run_tolerating_transient(
            'workflow_definition_tests',
            run_workflow_definition_tests, workflow_executor)
        _run_tolerating_transient(
            'workflow_execution_tests',
            run_workflow_execution_tests, configuration, workflow_executor)
        _run_tolerating_transient(
            'orkes_clients',
            TestOrkesClients(configuration=configuration).run)
        logger.info('END: integration tests')
