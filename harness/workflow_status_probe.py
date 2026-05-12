from __future__ import annotations

import collections
import random
import threading
from typing import Optional

from conductor.client.workflow_client import WorkflowClient


class WorkflowStatusProbe:
    """Probe that exercises UUID-bearing workflow lookup endpoints so
    ``http_api_client_request_seconds`` picks up entries with
    ``uri=/workflow/{workflowId}`` and ``uri=/workflow/{workflowId}/status``.

    Default off.  Runs only when ``HARNESS_PROBE_RATE_PER_SEC`` > 0.

    Side-effect-free: only issues read calls (``get_workflow`` and
    ``get_workflow_status``).

    Self-bounded: recently-started workflow IDs are kept in a fixed-size
    FIFO so memory is constant regardless of harness uptime.
    """

    MAX_TRACKED_IDS = 256

    def __init__(self, workflow_client: WorkflowClient, calls_per_second: int) -> None:
        self._workflow_client = workflow_client
        self._calls_per_second = calls_per_second
        self._recent_ids: collections.deque[str] = collections.deque(maxlen=self.MAX_TRACKED_IDS)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def offer(self, workflow_id: str) -> None:
        """Capture a workflow ID for later probing.  Thread-safe."""
        if not workflow_id:
            return
        with self._lock:
            self._recent_ids.appendleft(workflow_id)

    def start(self) -> None:
        if self._calls_per_second <= 0:
            print("WorkflowStatusProbe disabled (HARNESS_PROBE_RATE_PER_SEC<=0)")
            return
        print(
            f"WorkflowStatusProbe started: rate={self._calls_per_second}/sec, "
            f"retainedIds<={self.MAX_TRACKED_IDS}"
        )
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="WorkflowStatusProbe", daemon=True)
        self._thread.start()

    def shutdown(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._tick()
            self._stop_event.wait(timeout=1.0)

    def _tick(self) -> None:
        with self._lock:
            budget = min(self._calls_per_second, len(self._recent_ids))
            if budget == 0:
                return
            ids_to_probe = [self._recent_ids[i] for i in range(budget)]
            # Rotate: move probed IDs to the back
            for _ in range(budget):
                self._recent_ids.rotate(-1)

        for wf_id in ids_to_probe:
            try:
                if random.random() < 0.5:
                    self._workflow_client.get_workflow(wf_id, include_tasks=False)
                else:
                    self._workflow_client.get_workflow_status(wf_id)
            except Exception:
                pass
