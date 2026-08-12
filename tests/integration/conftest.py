"""
Shared fixtures and skip logic for integration tests.

When the Conductor server or credentials are unavailable, all integration
tests are skipped gracefully instead of failing with AuthorizationException
or connection errors.
"""

import logging
import unittest

import pytest

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api_client import ApiClient
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connectivity check (cached at module level, runs once per session)
# ---------------------------------------------------------------------------

_server_available = None  # None = not yet checked
_skip_reason = ""


def _check_server_connectivity():
    """
    Attempt a lightweight API call to verify the Conductor server is
    reachable and credentials (if required) are valid.

    Returns (is_available, skip_reason).
    """
    global _server_available, _skip_reason
    if _server_available is not None:
        return _server_available, _skip_reason

    try:
        config = Configuration()
        from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
        client = OrkesMetadataClient(config)
        client.get_all_task_defs()
        _server_available = True
        _skip_reason = ""
        logger.info("Conductor server is available at %s", config.host)
    except Exception as e:
        _server_available = False
        _skip_reason = f"Conductor server not available: {e}"
        logger.warning(_skip_reason)

    return _server_available, _skip_reason


def skip_if_server_unavailable():
    """
    Call from unittest.TestCase.setUpClass to skip the entire test class
    when the Conductor server is not available.

    Usage::

        @classmethod
        def setUpClass(cls):
            from tests.integration.conftest import skip_if_server_unavailable
            skip_if_server_unavailable()
            # ... rest of setup
    """
    available, reason = _check_server_connectivity()
    if not available:
        raise unittest.SkipTest(reason)


# ---------------------------------------------------------------------------
# Metadata cleanup
# ---------------------------------------------------------------------------

def cleanup_metadata(config, task_defs=(), workflow_defs=()):
    """Best-effort delete of metadata a test class registered.

    Suites that register per-run task defs (``worker_task(...,
    register_task_def=True)`` with a RUN_ID-suffixed name) used to leave every
    one behind, so each CI run added a handful to the shared server until it
    hit its Task Definitions cap and answered 402 to all further
    registrations. Call this from tearDownClass.

    Failures are logged and swallowed: cleanup must never turn a passing suite
    red, and a def that was never registered is nothing to report.

    ``workflow_defs`` items are names (version 1 assumed) or (name, version).
    """
    from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient

    client = OrkesMetadataClient(config)

    for name in task_defs:
        try:
            client.unregister_task_def(name)
        except Exception as e:
            logger.warning("cleanup: could not unregister task def %s: %s", name, e)

    for entry in workflow_defs:
        name, version = entry if isinstance(entry, tuple) else (entry, 1)
        try:
            client.unregister_workflow_def(name, version)
        except Exception as e:
            logger.warning(
                "cleanup: could not unregister workflow def %s v%s: %s", name, version, e
            )


# ---------------------------------------------------------------------------
# Pytest session-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def conductor_config():
    """Provide a Configuration connected to the Conductor server, or skip."""
    available, reason = _check_server_connectivity()
    if not available:
        pytest.skip(reason)
    return Configuration()


@pytest.fixture(scope="session")
def api_client(conductor_config):
    """Provide an ApiClient instance for integration tests."""
    return ApiClient(conductor_config)


@pytest.fixture(scope="session")
def workflow_executor(conductor_config):
    """Provide a WorkflowExecutor instance for integration tests."""
    return WorkflowExecutor(conductor_config)


@pytest.fixture(scope="session")
def workflow_quantity():
    """Default number of workflows to run in execution tests."""
    return 6


# ---------------------------------------------------------------------------
# Autouse fixture: skip ALL pytest-native integration tests when server
# is unavailable. (unittest.TestCase tests need skip_if_server_unavailable()
# in setUpClass instead — autouse fixtures don't apply to them.)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _skip_integration_if_no_server():
    """Skip every integration test when the Conductor server is not reachable."""
    available, reason = _check_server_connectivity()
    if not available:
        pytest.skip(reason)
