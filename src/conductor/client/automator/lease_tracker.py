"""Centralized lease extension (heartbeat) management for Conductor task runners.

Architecture:
    LeaseManager runs a single background daemon thread that periodically checks
    for tasks needing lease extension heartbeats. Due heartbeats are dispatched
    to a small fixed ThreadPoolExecutor for parallel, non-blocking API calls.

    This decouples heartbeat work entirely from worker poll loops, preventing
    heartbeat API calls (and their retries) from blocking task polling.

    Thread-safe: track() and untrack() can be called from any thread or event loop.
"""

import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, Optional

from conductor.client.http.models.task_result import TaskResult

logger = logging.getLogger(__name__)

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
    task_client: Any = None     # Sync TaskResourceApi for sending heartbeats


class LeaseManager:
    """Centralized lease extension manager for all workers in a process.

    One background daemon thread checks for due heartbeats at a fixed interval.
    A small ThreadPoolExecutor sends heartbeat API calls in parallel.
    Poll loops are never blocked by heartbeat work.

    Usage:
        manager = LeaseManager.get_instance()
        manager.track(task_id, workflow_id, timeout, task_client)
        # ... task completes ...
        manager.untrack(task_id)
    """

    _instance: Optional['LeaseManager'] = None
    _instance_lock = threading.Lock()
    _instance_pid: Optional[int] = None

    @classmethod
    def get_instance(cls, check_interval: float = 1.0,
                     max_heartbeat_workers: int = 4) -> 'LeaseManager':
        """Get or create the process-wide LeaseManager singleton.

        Fork-safe: a new instance is created after fork (threads don't survive fork).
        """
        current_pid = os.getpid()
        if cls._instance is None or cls._instance_pid != current_pid:
            with cls._instance_lock:
                if cls._instance is None or cls._instance_pid != current_pid:
                    cls._instance = cls(
                        check_interval=check_interval,
                        max_heartbeat_workers=max_heartbeat_workers,
                    )
                    cls._instance_pid = current_pid
        return cls._instance

    @classmethod
    def _reset_instance(cls):
        """Reset the singleton. For testing only."""
        with cls._instance_lock:
            if cls._instance is not None:
                cls._instance.shutdown()
            cls._instance = None
            cls._instance_pid = None

    def __init__(self, check_interval: float = 1.0, max_heartbeat_workers: int = 4):
        self._tracked: Dict[str, LeaseInfo] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(
            max_workers=max_heartbeat_workers,
            thread_name_prefix="lease-heartbeat",
        )
        self._stop_event = threading.Event()
        self._check_interval = check_interval
        self._thread: Optional[threading.Thread] = None
        self._started = False
        self._start_lock = threading.Lock()

    def _ensure_started(self) -> None:
        """Lazily start the background thread on first track() call."""
        if self._started:
            return
        with self._start_lock:
            if not self._started:
                self._thread = threading.Thread(
                    target=self._run, daemon=True, name="lease-manager",
                )
                self._thread.start()
                self._started = True
                logger.debug(
                    "LeaseManager started (check_interval=%.1fs)", self._check_interval,
                )

    def track(self, task_id: str, workflow_instance_id: str,
              response_timeout_seconds: float, task_client: Any) -> None:
        """Start tracking a task for lease extension heartbeats.

        Thread-safe. Can be called from any worker thread or event loop.

        Args:
            task_id: Conductor task ID.
            workflow_instance_id: Workflow instance this task belongs to.
            response_timeout_seconds: The task's server-side response timeout.
            task_client: A **sync** TaskResourceApi for sending heartbeat API calls.
        """
        interval = response_timeout_seconds * LEASE_EXTEND_DURATION_FACTOR
        if interval < 1:
            logger.debug(
                "Skipping lease tracking for task %s (interval %.1fs too short)",
                task_id, interval,
            )
            return

        info = LeaseInfo(
            task_id=task_id,
            workflow_instance_id=workflow_instance_id,
            response_timeout_seconds=response_timeout_seconds,
            last_heartbeat_time=time.monotonic(),
            interval_seconds=interval,
            task_client=task_client,
        )
        with self._lock:
            self._tracked[task_id] = info
        self._ensure_started()
        logger.debug(
            "Tracking lease for task %s (timeout=%ss, heartbeat every %ss)",
            task_id, response_timeout_seconds, interval,
        )

    def untrack(self, task_id: str) -> None:
        """Stop tracking a task. Thread-safe."""
        with self._lock:
            removed = self._tracked.pop(task_id, None)
        if removed is not None:
            logger.debug("Untracked lease for task %s", task_id)

    @property
    def tracked_count(self) -> int:
        """Number of currently tracked tasks."""
        with self._lock:
            return len(self._tracked)

    # -- Background thread -----------------------------------------------------

    def _run(self) -> None:
        """Background loop — checks for due heartbeats at fixed intervals."""
        while not self._stop_event.is_set():
            try:
                self._check_and_send()
            except Exception as e:
                logger.error("LeaseManager error: %s", e)
            self._stop_event.wait(self._check_interval)

    def _check_and_send(self) -> None:
        """Find tasks with due heartbeats and dispatch to the thread pool."""
        now = time.monotonic()
        with self._lock:
            due = [
                info for info in self._tracked.values()
                if now - info.last_heartbeat_time >= info.interval_seconds
            ]
        for info in due:
            # Update timestamp immediately to prevent double-dispatch on next tick
            info.last_heartbeat_time = time.monotonic()
            self._executor.submit(self._send_heartbeat, info)

    @staticmethod
    def _send_heartbeat(info: LeaseInfo) -> None:
        """Send a single lease extension heartbeat with retry.

        Runs in a pool thread — blocking retries only block the pool thread,
        never a poll loop.
        """
        result = TaskResult(
            task_id=info.task_id,
            workflow_instance_id=info.workflow_instance_id,
            extend_lease=True,
        )
        for attempt in range(LEASE_EXTEND_RETRY_COUNT):
            try:
                info.task_client.update_task(body=result)
                logger.debug("Extended lease for task %s", info.task_id)
                return
            except Exception as e:
                if attempt < LEASE_EXTEND_RETRY_COUNT - 1:
                    time.sleep(0.5 * (attempt + 2))
                else:
                    logger.error(
                        "Failed to extend lease for task %s after %d attempts: %s",
                        info.task_id, LEASE_EXTEND_RETRY_COUNT, e,
                    )

    # -- Lifecycle -------------------------------------------------------------

    def shutdown(self) -> None:
        """Stop the background thread and thread pool."""
        self._stop_event.set()
        if self._started and self._thread is not None:
            self._thread.join(timeout=5)
        self._executor.shutdown(wait=False)
        with self._lock:
            self._tracked.clear()
        logger.debug("LeaseManager shut down")
