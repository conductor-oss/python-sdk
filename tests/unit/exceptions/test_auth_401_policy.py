import pytest
import time
from unittest.mock import Mock, patch

from conductor.client.exceptions.auth_401_policy import Auth401Policy, Auth401Handler


class TestAuth401Policy:
    def test_is_401_unauthorized(self):
        policy = Auth401Policy()

        assert policy.is_401_unauthorized(401) is True
        assert policy.is_401_unauthorized(403) is False
        assert policy.is_401_unauthorized(400) is False
        assert policy.is_401_unauthorized(500) is False

    def test_is_auth_dependent_call(self):
        policy = Auth401Policy()

        # Auth-dependent calls
        assert policy.is_auth_dependent_call("/workflow/start", "POST") is True
        assert policy.is_auth_dependent_call("/task/poll", "GET") is True
        assert policy.is_auth_dependent_call("/metadata/workflow", "GET") is True
        assert policy.is_auth_dependent_call("/scheduler/schedule", "POST") is True
        assert policy.is_auth_dependent_call("/secret/get", "GET") is True
        assert policy.is_auth_dependent_call("/prompt/template", "GET") is True
        assert policy.is_auth_dependent_call("/schema/validate", "POST") is True
        assert (
            policy.is_auth_dependent_call("/service-registry/register", "POST") is True
        )

        # Non-auth-dependent calls
        assert policy.is_auth_dependent_call("/token", "POST") is False
        assert policy.is_auth_dependent_call("/auth/login", "POST") is False
        assert policy.is_auth_dependent_call("/health", "GET") is False
        assert policy.is_auth_dependent_call("/status", "GET") is False

    def test_should_retry_401(self):
        policy = Auth401Policy(max_attempts=3)

        # Should retry when under max attempts
        assert policy.should_retry_401("/workflow/start") is True
        policy.record_401_attempt("/workflow/start")
        assert policy.should_retry_401("/workflow/start") is True
        policy.record_401_attempt("/workflow/start")
        assert policy.should_retry_401("/workflow/start") is True

        # Should not retry when at max attempts
        policy.record_401_attempt("/workflow/start")
        assert policy.should_retry_401("/workflow/start") is False

    def test_record_401_attempt(self):
        policy = Auth401Policy()

        assert policy.get_attempt_count("/workflow/start") == 0
        policy.record_401_attempt("/workflow/start")
        assert policy.get_attempt_count("/workflow/start") == 1
        policy.record_401_attempt("/workflow/start")
        assert policy.get_attempt_count("/workflow/start") == 2

    def test_record_success_resets_attempts(self):
        policy = Auth401Policy()

        # Record some 401 attempts
        policy.record_401_attempt("/workflow/start")
        policy.record_401_attempt("/workflow/start")
        assert policy.get_attempt_count("/workflow/start") == 2

        # Record success should reset
        policy.record_success("/workflow/start")
        assert policy.get_attempt_count("/workflow/start") == 0

    def test_get_retry_delay_exponential_backoff(self):
        policy = Auth401Policy(base_delay_ms=1000, max_delay_ms=10000)

        # First attempt should be around base delay * 2 (in seconds)
        policy.record_401_attempt("/workflow/start")
        delay1 = policy.get_retry_delay("/workflow/start")
        assert 1.6 <= delay1 <= 2.4  # base * 2 ± 20% jitter (converted to seconds)

        # Second attempt should be double
        policy.record_401_attempt("/workflow/start")
        delay2 = policy.get_retry_delay("/workflow/start")
        assert delay2 > delay1

        # Third attempt should be double again
        policy.record_401_attempt("/workflow/start")
        delay3 = policy.get_retry_delay("/workflow/start")
        assert delay3 > delay2

    def test_get_retry_delay_respects_max_delay(self):
        policy = Auth401Policy(base_delay_ms=1000, max_delay_ms=5000)

        # Make many attempts to exceed max delay
        for _ in range(10):
            policy.record_401_attempt("/workflow/start")

        delay = policy.get_retry_delay("/workflow/start")
        assert delay <= 5.0  # max_delay_ms converted to seconds

    def test_should_stop_worker(self):
        policy = Auth401Policy(max_attempts=3)

        # Should not stop before max attempts
        assert policy.should_stop_worker("/workflow/start") is False
        policy.record_401_attempt("/workflow/start")
        assert policy.should_stop_worker("/workflow/start") is False
        policy.record_401_attempt("/workflow/start")
        assert policy.should_stop_worker("/workflow/start") is False

        # Should stop at max attempts
        policy.record_401_attempt("/workflow/start")
        assert policy.should_stop_worker("/workflow/start") is True


class TestAuth401Handler:
    def test_handle_401_error_auth_dependent(self):
        handler = Auth401Handler()

        result = handler.handle_401_error(
            resource_path="/workflow/start",
            method="POST",
            status_code=401,
            error_code="INVALID_TOKEN",
        )

        assert result["should_retry"] is True
        assert result["delay_seconds"] > 0
        assert result["should_stop_worker"] is False
        assert result["attempt_count"] == 1
        assert result["max_attempts"] == 6

    def test_handle_401_error_non_auth_dependent(self):
        handler = Auth401Handler()

        result = handler.handle_401_error(
            resource_path="/token",
            method="POST",
            status_code=401,
            error_code="INVALID_TOKEN",
        )

        assert result["should_retry"] is False
        assert result["delay_seconds"] == 0.0
        assert result["should_stop_worker"] is False
        assert result["attempt_count"] == 0

    def test_handle_401_error_non_401_status(self):
        handler = Auth401Handler()

        result = handler.handle_401_error(
            resource_path="/workflow/start",
            method="POST",
            status_code=403,
            error_code="FORBIDDEN",
        )

        assert result["should_retry"] is False
        assert result["delay_seconds"] == 0.0
        assert result["should_stop_worker"] is False
        assert result["attempt_count"] == 0

    def test_handle_401_error_max_attempts_reached(self):
        handler = Auth401Handler(Auth401Policy(max_attempts=2))

        # First attempt
        result1 = handler.handle_401_error(
            resource_path="/workflow/start",
            method="POST",
            status_code=401,
            error_code="INVALID_TOKEN",
        )
        assert result1["should_retry"] is True
        assert result1["should_stop_worker"] is False

        # Second attempt (max reached)
        result2 = handler.handle_401_error(
            resource_path="/workflow/start",
            method="POST",
            status_code=401,
            error_code="INVALID_TOKEN",
        )
        assert result2["should_retry"] is False
        assert result2["should_stop_worker"] is True
        assert result2["attempt_count"] == 2

    def test_record_successful_call(self):
        handler = Auth401Handler()

        # Record some 401 attempts
        handler.handle_401_error("/workflow/start", "POST", 401, "INVALID_TOKEN")
        handler.handle_401_error("/workflow/start", "POST", 401, "INVALID_TOKEN")
        assert handler.policy.get_attempt_count("/workflow/start") == 2

        # Record success should reset
        handler.record_successful_call("/workflow/start")
        assert handler.policy.get_attempt_count("/workflow/start") == 0

    def test_is_worker_stopped(self):
        handler = Auth401Handler(Auth401Policy(max_attempts=1))

        assert handler.is_worker_stopped() is False

        # Trigger max attempts
        handler.handle_401_error("/workflow/start", "POST", 401, "INVALID_TOKEN")
        assert handler.is_worker_stopped() is True

    def test_reset_worker(self):
        handler = Auth401Handler(Auth401Policy(max_attempts=1))

        # Stop the worker
        handler.handle_401_error("/workflow/start", "POST", 401, "INVALID_TOKEN")
        assert handler.is_worker_stopped() is True

        # Reset should allow worker to continue
        handler.reset_worker()
        assert handler.is_worker_stopped() is False

    @patch("conductor.client.exceptions.auth_401_policy.logger")
    def test_handle_401_error_logging(self, mock_logger):
        handler = Auth401Handler()

        # Test retry logging
        handler.handle_401_error("/workflow/start", "POST", 401, "INVALID_TOKEN")
        assert mock_logger.warning.called

        # Test max attempts logging
        handler = Auth401Handler(Auth401Policy(max_attempts=1))
        handler.handle_401_error("/workflow/start", "POST", 401, "INVALID_TOKEN")
        assert mock_logger.error.called

    def test_different_endpoints_independent_tracking(self):
        handler = Auth401Handler(Auth401Policy(max_attempts=2))

        # Track attempts for different endpoints independently
        handler.handle_401_error("/workflow/start", "POST", 401, "INVALID_TOKEN")
        handler.handle_401_error("/task/poll", "GET", 401, "INVALID_TOKEN")

        # Each endpoint should have its own attempt count
        assert handler.policy.get_attempt_count("/workflow/start") == 1
        assert handler.policy.get_attempt_count("/task/poll") == 1

        # Success on one endpoint shouldn't affect the other
        handler.record_successful_call("/workflow/start")
        assert handler.policy.get_attempt_count("/workflow/start") == 0
        assert handler.policy.get_attempt_count("/task/poll") == 1
