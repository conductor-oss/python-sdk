import os
import pytest
import uuid
from typing import Optional

from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_authorization_client import OrkesAuthorizationClient
from conductor.client.http.models.upsert_user_request import (
    UpsertUserRequestAdapter as UpsertUserRequest,
)


@pytest.fixture(scope="session")
def conductor_configuration():
    """
    Create a Conductor configuration from environment variables.

    Environment Variables:
    - CONDUCTOR_SERVER_URL: Base URL for Conductor server
    - CONDUCTOR_AUTH_KEY: Authentication key for Orkes
    - CONDUCTOR_AUTH_SECRET: Authentication secret for Orkes
    - CONDUCTOR_UI_SERVER_URL: UI server URL (optional)
    - CONDUCTOR_DEBUG: Enable debug logging (default: false)
    """
    config = Configuration()

    config.debug = os.getenv("CONDUCTOR_DEBUG", "false").lower() == "true"

    config.apply_logging_config()

    return config


@pytest.fixture(scope="session")
def test_timeout():
    """Get test timeout from environment variable."""
    return int(os.getenv("CONDUCTOR_TEST_TIMEOUT", "30"))


@pytest.fixture(scope="session")
def cleanup_enabled():
    """Check if test cleanup is enabled."""
    return os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true"


@pytest.fixture(scope="session")
def skip_performance_tests():
    """Check if performance tests should be skipped."""
    return os.getenv("CONDUCTOR_SKIP_PERFORMANCE_TESTS", "false").lower() == "true"


@pytest.fixture(scope="session")
def test_suffix():
    """Generate unique suffix for test resources."""
    return str(uuid.uuid4())[:8]


@pytest.fixture(scope="session")
def authorization_client(conductor_configuration):
    """Create OrkesAuthorizationClient instance."""
    return OrkesAuthorizationClient(conductor_configuration)


@pytest.fixture(scope="function")
def test_user_id(test_suffix):
    """Generate test user ID."""
    return f"test_user_{test_suffix}@example.com"


@pytest.fixture(scope="function")
def test_user(authorization_client, test_user_id, cleanup_enabled):
    """
    Create a test user and clean it up after the test.

    Args:
        authorization_client: OrkesAuthorizationClient instance
        test_user_id: Unique test user ID
        cleanup_enabled: Whether to cleanup test resources

    Yields:
        dict: Created user object with id, name, and roles
    """
    create_request = UpsertUserRequest(name="Test User", roles=["USER"])
    created_user = authorization_client.upsert_user(create_request, test_user_id)

    user_data = {
        "id": created_user.id,
        "name": created_user.name,
        "roles": (
            [role.name for role in created_user.roles] if created_user.roles else []
        ),
    }

    yield user_data

    if cleanup_enabled:
        try:
            authorization_client.delete_user(test_user_id)
        except Exception:
            pass


@pytest.fixture(scope="function")
def test_user_with_roles(authorization_client, test_user_id, cleanup_enabled):
    """
    Create a test user with specific roles and clean it up after the test.

    Args:
        authorization_client: OrkesAuthorizationClient instance
        test_user_id: Unique test user ID
        cleanup_enabled: Whether to cleanup test resources

    Yields:
        dict: Created user object with id, name, and roles
    """
    create_request = UpsertUserRequest(
        name="Test User with Roles", roles=["USER", "ADMIN"]
    )
    created_user = authorization_client.upsert_user(create_request, test_user_id)

    user_data = {
        "id": created_user.id,
        "name": created_user.name,
        "roles": (
            [role.name for role in created_user.roles] if created_user.roles else []
        ),
    }

    yield user_data

    if cleanup_enabled:
        try:
            authorization_client.delete_user(test_user_id)
        except Exception:
            pass


@pytest.fixture(scope="function")
def test_user_basic(authorization_client, test_user_id, cleanup_enabled):
    """
    Create a basic test user (no roles) and clean it up after the test.

    Args:
        authorization_client: OrkesAuthorizationClient instance
        test_user_id: Unique test user ID
        cleanup_enabled: Whether to cleanup test resources

    Yields:
        dict: Created user object with id, name, and roles
    """
    create_request = UpsertUserRequest(name="Basic Test User", roles=[])
    created_user = authorization_client.upsert_user(create_request, test_user_id)

    user_data = {
        "id": created_user.id,
        "name": created_user.name,
        "roles": (
            [role.name for role in created_user.roles] if created_user.roles else []
        ),
    }

    yield user_data

    if cleanup_enabled:
        try:
            authorization_client.delete_user(test_user_id)
        except Exception:
            pass


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "slow: mark test as slow running test")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)

        if "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.performance)

        if any(
            keyword in item.nodeid.lower()
            for keyword in ["concurrent", "bulk", "performance"]
        ):
            item.add_marker(pytest.mark.slow)
