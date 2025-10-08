import logging
import random
import time
from typing import Optional

logger = logging.getLogger(__name__)


class Auth401Policy:
    """
    Policy for handling HTTP 401 errors with exponential backoff and fail-stop behavior.
    Only applies to auth-dependent calls, not to 400/403/5xx errors.
    """

    def __init__(
        self,
        max_attempts: int = 6,
        base_delay_ms: float = 1000.0,
        max_delay_ms: float = 60000.0,
        jitter_percent: float = 0.2,
        stop_behavior: str = "stop_worker",
    ):
        self.max_attempts = max_attempts
        self.base_delay_ms = base_delay_ms
        self.max_delay_ms = max_delay_ms
        self.jitter_percent = jitter_percent
        self.stop_behavior = stop_behavior

        # Track attempts per endpoint to allow reset on success
        self._attempt_counts = {}
        self._last_success_time = {}

    def is_401_unauthorized(self, status_code: int) -> bool:
        """Check if the status code is specifically 401 (not 403 or other auth errors)."""
        return status_code == 401

    def is_auth_dependent_call(self, resource_path: str, method: str = None) -> bool:
        """
        Determine if a call requires authentication and should be subject to 401 policy.
        Excludes token refresh endpoints and other non-auth calls.
        """
        # Suppress unused parameter warning
        _ = method
        # Token refresh endpoints should not trigger 401 policy
        if "/token" in resource_path.lower() or "/auth" in resource_path.lower():
            return False

        # Auth-dependent endpoints that should trigger 401 policy
        auth_endpoints = [
            "/workflow",
            "/task",
            "/metadata",
            "/scheduler",
            "/secret",
            "/prompt",
            "/schema",
            "/service-registry",
        ]

        # Check if this is an auth-dependent endpoint
        return any(endpoint in resource_path for endpoint in auth_endpoints)

    def should_retry_401(self, resource_path: str) -> bool:
        """
        Determine if a 401 error should be retried based on attempt count and policy.
        """
        attempt_count = self._attempt_counts.get(resource_path, 0)
        return attempt_count < self.max_attempts

    def record_401_attempt(self, resource_path: str) -> None:
        """Record a 401 attempt for tracking purposes."""
        self._attempt_counts[resource_path] = (
            self._attempt_counts.get(resource_path, 0) + 1
        )

    def record_success(self, resource_path: str) -> None:
        """Record a successful call to reset attempt counters."""
        self._attempt_counts[resource_path] = 0
        self._last_success_time[resource_path] = time.time()

    def get_retry_delay(self, resource_path: str) -> float:
        """
        Calculate exponential backoff delay with jitter for 401 retries.
        """
        attempt_count = self._attempt_counts.get(resource_path, 0)

        # Exponential backoff
        delay_ms = self.base_delay_ms * (2**attempt_count)

        # Add jitter: ±jitter_percent of the delay (before capping)
        jitter_range = delay_ms * self.jitter_percent
        jitter = random.uniform(-jitter_range, jitter_range)
        delay_ms = delay_ms + jitter

        # Apply max delay cap after jitter to ensure we never exceed the max
        delay_ms = min(max(0, delay_ms), self.max_delay_ms)

        return delay_ms / 1000.0  # Convert to seconds

    def should_stop_worker(self, resource_path: str) -> bool:
        """
        Determine if the worker should stop after max 401 attempts.
        """
        attempt_count = self._attempt_counts.get(resource_path, 0)
        return attempt_count >= self.max_attempts

    def get_attempt_count(self, resource_path: str) -> int:
        """Get current attempt count for a resource path."""
        return self._attempt_counts.get(resource_path, 0)

    def reset_attempts(self, resource_path: str) -> None:
        """Reset attempt count for a resource path (called after successful auth)."""
        self._attempt_counts[resource_path] = 0


class Auth401Handler:
    """
    Handler for 401 errors that integrates with the existing conductor client.
    """

    def __init__(self, policy: Optional[Auth401Policy] = None):
        self.policy = policy or Auth401Policy()
        self._worker_stopped = False

    def handle_401_error(
        self,
        resource_path: str,
        method: str,
        status_code: int,
        error_code: Optional[str] = None,
    ) -> dict:
        """
        Handle a 401 error according to the policy.

        Returns:
            dict: {
                'should_retry': bool,
                'delay_seconds': float,
                'should_stop_worker': bool,
                'attempt_count': int,
                'max_attempts': int
            }
        """
        # Suppress unused parameter warning
        _ = error_code
        # Only handle 401 errors on auth-dependent calls
        if not self.policy.is_401_unauthorized(status_code):
            return {
                "should_retry": False,
                "delay_seconds": 0.0,
                "should_stop_worker": False,
                "attempt_count": 0,
                "max_attempts": self.policy.max_attempts,
            }

        if not self.policy.is_auth_dependent_call(resource_path, method):
            logger.debug(
                "401 error on non-auth-dependent call %s %s - not applying 401 policy",
                method,
                resource_path,
            )
            return {
                "should_retry": False,
                "delay_seconds": 0.0,
                "should_stop_worker": False,
                "attempt_count": 0,
                "max_attempts": self.policy.max_attempts,
            }

        # Record the 401 attempt
        self.policy.record_401_attempt(resource_path)
        attempt_count = self.policy.get_attempt_count(resource_path)

        # Check if we should retry
        should_retry = self.policy.should_retry_401(resource_path)
        delay_seconds = 0.0

        if should_retry:
            delay_seconds = self.policy.get_retry_delay(resource_path)
            logger.warning(
                "401 error on %s %s (attempt %d/%d) - retrying in %.2fs",
                method,
                resource_path,
                attempt_count,
                self.policy.max_attempts,
                delay_seconds,
            )
        else:
            logger.error(
                "401 error on %s %s (attempt %d/%d) - max attempts reached, stopping worker",
                method,
                resource_path,
                attempt_count,
                self.policy.max_attempts,
            )

        # Check if worker should stop
        should_stop_worker = self.policy.should_stop_worker(resource_path)
        if should_stop_worker:
            self._worker_stopped = True
            logger.error(
                "Worker stopped due to persistent 401 errors on %s %s after %d attempts",
                method,
                resource_path,
                attempt_count,
            )

        return {
            "should_retry": should_retry,
            "delay_seconds": delay_seconds,
            "should_stop_worker": should_stop_worker,
            "attempt_count": attempt_count,
            "max_attempts": self.policy.max_attempts,
        }

    def record_successful_call(self, resource_path: str) -> None:
        """Record a successful call to reset 401 attempt counters."""
        self.policy.record_success(resource_path)
        logger.debug("Successful call to %s - reset 401 attempt counter", resource_path)

    def is_worker_stopped(self) -> bool:
        """Check if the worker has been stopped due to 401 errors."""
        return self._worker_stopped

    def reset_worker(self) -> None:
        """Reset the worker stop flag (for testing or recovery)."""
        self._worker_stopped = False
