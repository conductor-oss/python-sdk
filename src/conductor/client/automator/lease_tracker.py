"""Shared lease extension (heartbeat) tracking for TaskRunner and AsyncTaskRunner."""

from dataclasses import dataclass

# Lease extension constants (matches Java SDK)
LEASE_EXTEND_RETRY_COUNT = 3
LEASE_EXTEND_DURATION_FACTOR = 0.8


@dataclass
class LeaseInfo:
    """Tracks when a heartbeat is next due for an in-flight task."""
    task_id: str
    workflow_instance_id: str
    response_timeout_seconds: float
    last_heartbeat_time: float  # time.monotonic() of last heartbeat (or task start)
    interval_seconds: float     # 80% of responseTimeoutSeconds
