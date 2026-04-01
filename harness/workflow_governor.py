from __future__ import annotations

import threading
import time

from conductor.client.http.models import StartWorkflowRequest
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor


class WorkflowGovernor:

    def __init__(
        self,
        workflow_executor: WorkflowExecutor,
        workflow_name: str,
        workflows_per_second: int,
    ) -> None:
        self._workflow_executor = workflow_executor
        self._workflow_name = workflow_name
        self._workflows_per_second = workflows_per_second
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        print(
            f"WorkflowGovernor started: workflow={self._workflow_name}, "
            f"rate={self._workflows_per_second}/sec"
        )
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="WorkflowGovernor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        print("WorkflowGovernor stopped")

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._start_batch()
            self._stop_event.wait(timeout=1.0)

    def _start_batch(self) -> None:
        try:
            for _ in range(self._workflows_per_second):
                request = StartWorkflowRequest(name=self._workflow_name, version=1)
                self._workflow_executor.start_workflow(request)
            print(f"Governor: started {self._workflows_per_second} workflow(s)")
        except Exception as e:
            print(f"Governor: error starting workflows: {e}")
