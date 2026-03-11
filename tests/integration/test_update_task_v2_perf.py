"""
Performance test for update-task-v2 (tight execute loop).

Measures task queue wait time — the time a task sits scheduled before a worker
picks it up.  With the v2 endpoint the worker receives the next task in the
update response, so consecutive same-type tasks should have near-zero queue
latency (<20 ms).

Workflow shape (10 tasks, 3 types, same-type tasks consecutive):

    type_a_1 → type_a_2 → type_a_3 → type_a_4
             → type_b_1 → type_b_2 → type_b_3
             → type_c_1 → type_c_2 → type_c_3

Run (fixed 1 000 workflows — default):

    python -m pytest tests/integration/test_update_task_v2_perf.py -v -s

Run (duration-based, 1 hour):

    PERF_DURATION_MINUTES=60 python -m pytest tests/integration/test_update_task_v2_perf.py -v -s

Env-vars:
    PERF_WORKFLOW_COUNT   – number of workflows (default 1000, ignored when duration is set)
    PERF_DURATION_MINUTES – run for this many minutes instead of a fixed count
    PERF_RATE             – workflows submitted per second (default 20)
    PERF_WORKER_THREADS   – thread_count per worker type (default 10)
"""

import logging
import os
import statistics
import sys
import time
import threading
import unittest
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.start_workflow_request import StartWorkflowRequest
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.http.models.workflow_task import WorkflowTask
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient
from conductor.client.worker.worker_task import worker_task

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WORKFLOW_NAME = "perf_v2_update_test"
WORKFLOW_VERSION = 1

TASK_SEQUENCE = [
    ("perf_type_a", 4),
    ("perf_type_b", 3),
    ("perf_type_c", 3),
]

WORKER_THREADS = int(os.environ.get("PERF_WORKER_THREADS", "10"))
WORKFLOW_COUNT = int(os.environ.get("PERF_WORKFLOW_COUNT", "1000"))
DURATION_MINUTES = float(os.environ.get("PERF_DURATION_MINUTES", "0"))
SUBMIT_RATE = float(os.environ.get("PERF_RATE", "20"))  # workflows/sec

# ---------------------------------------------------------------------------
# Workers — near-zero execution time so we isolate queue latency
# ---------------------------------------------------------------------------

@worker_task(task_definition_name="perf_type_a", thread_count=WORKER_THREADS, register_task_def=True)
async def perf_worker_a(task_index: int = 0) -> dict:
    return {"worker": "perf_type_a", "task_index": task_index}


@worker_task(task_definition_name="perf_type_b", thread_count=WORKER_THREADS, register_task_def=True)
async def perf_worker_b(task_index: int = 0) -> dict:
    return {"worker": "perf_type_b", "task_index": task_index}


@worker_task(task_definition_name="perf_type_c", thread_count=WORKER_THREADS, register_task_def=True)
async def perf_worker_c(task_index: int = 0) -> dict:
    return {"worker": "perf_type_c", "task_index": task_index}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_workflow_tasks() -> list:
    tasks = []
    idx = 0
    for task_type, count in TASK_SEQUENCE:
        for i in range(count):
            idx += 1
            tasks.append(
                WorkflowTask(
                    name=task_type,
                    task_reference_name=f"{task_type}_{i + 1}",
                    input_parameters={"task_index": idx},
                )
            )
    return tasks


def _percentile(data: list, p: float) -> float:
    if not data:
        return 0.0
    k = (len(data) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(data):
        return data[f]
    return data[f] + (k - f) * (data[c] - data[f])


def _print_latency_report(queue_times_by_task: dict, workflow_durations: list,
                           elapsed: float, total_workflows: int):
    print("\n" + "=" * 90)
    print(f"  PERFORMANCE REPORT  —  {total_workflows} workflows in {elapsed:.1f}s "
          f"({total_workflows / max(elapsed, 0.001):.1f} wf/s)")
    print("=" * 90)

    print(f"\n{'Task Ref':<20} {'Count':>6} {'Mean':>8} {'p50':>8} {'p90':>8} "
          f"{'p95':>8} {'p99':>8} {'Max':>8}")
    print("-" * 90)

    all_queue_times = []
    for ref in sorted(queue_times_by_task.keys()):
        times = sorted(queue_times_by_task[ref])
        all_queue_times.extend(times)
        mean = statistics.mean(times)
        p50 = _percentile(times, 50)
        p90 = _percentile(times, 90)
        p95 = _percentile(times, 95)
        p99 = _percentile(times, 99)
        mx = max(times)
        print(f"{ref:<20} {len(times):>6} {mean:>7.0f}ms {p50:>7.0f}ms "
              f"{p90:>7.0f}ms {p95:>7.0f}ms {p99:>7.0f}ms {mx:>7.0f}ms")

    all_queue_times.sort()
    if all_queue_times:
        print("-" * 90)
        print(f"{'ALL TASKS':<20} {len(all_queue_times):>6} "
              f"{statistics.mean(all_queue_times):>7.0f}ms "
              f"{_percentile(all_queue_times, 50):>7.0f}ms "
              f"{_percentile(all_queue_times, 90):>7.0f}ms "
              f"{_percentile(all_queue_times, 95):>7.0f}ms "
              f"{_percentile(all_queue_times, 99):>7.0f}ms "
              f"{max(all_queue_times):>7.0f}ms")

    if workflow_durations:
        workflow_durations.sort()
        print(f"\n{'Workflow E2E':<20} {len(workflow_durations):>6} "
              f"{statistics.mean(workflow_durations):>7.0f}ms "
              f"{_percentile(workflow_durations, 50):>7.0f}ms "
              f"{_percentile(workflow_durations, 90):>7.0f}ms "
              f"{_percentile(workflow_durations, 95):>7.0f}ms "
              f"{_percentile(workflow_durations, 99):>7.0f}ms "
              f"{max(workflow_durations):>7.0f}ms")

    print("=" * 90 + "\n")


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

class TestUpdateTaskV2Perf(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from tests.integration.conftest import skip_if_server_unavailable
        skip_if_server_unavailable()

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(process)d] %(name)-45s %(levelname)-10s %(message)s",
        )
        logging.getLogger("conductor.client").setLevel(logging.WARNING)

        cls.config = Configuration()
        cls.workflow_client = OrkesWorkflowClient(cls.config)
        cls.metadata_client = OrkesMetadataClient(cls.config)

    # ---- setup ----------------------------------------------------------

    def test_0_register_workflow(self):
        """Register the performance-test workflow definition."""
        workflow = WorkflowDef(name=WORKFLOW_NAME, version=WORKFLOW_VERSION)
        workflow._tasks = _build_workflow_tasks()
        try:
            self.metadata_client.update_workflow_def(workflow, overwrite=True)
        except Exception:
            self.metadata_client.register_workflow_def(workflow, overwrite=True)
        print(f"\n✓ Registered workflow '{WORKFLOW_NAME}' with {len(workflow._tasks)} tasks")

    # ---- main perf test -------------------------------------------------

    def test_1_run_perf(self):
        """Start workers, fire workflows at a controlled rate, collect queue-wait latencies."""

        handler_ready = threading.Event()
        handler_ref = {}

        def _run_workers():
            handler = TaskHandler(
                configuration=self.config,
                scan_for_annotated_workers=True,
            )
            handler_ref["h"] = handler
            handler.start_processes()
            handler_ready.set()
            handler_ref["stop"] = threading.Event()
            handler_ref["stop"].wait()
            handler.stop_processes()

        worker_thread = threading.Thread(target=_run_workers, daemon=True)
        worker_thread.start()
        handler_ready.wait(timeout=30)
        self.assertTrue(handler_ready.is_set(), "Workers failed to start within 30s")
        # Let workers warm up — establish polling loops
        time.sleep(5)
        print(f"\n✓ Workers started ({WORKER_THREADS} threads/type, warmed up)")

        try:
            if DURATION_MINUTES > 0:
                self._run_duration_mode()
            else:
                self._run_fixed_count_mode()
        finally:
            handler_ref.get("stop", threading.Event()).set()
            worker_thread.join(timeout=15)

    # ---- fixed-count mode -----------------------------------------------

    def _run_fixed_count_mode(self):
        total = WORKFLOW_COUNT
        interval = 1.0 / SUBMIT_RATE
        print(f"\n→ Fixed-count mode: {total} workflows at {SUBMIT_RATE} wf/s")

        workflow_ids = []
        start_time = time.time()

        for i in range(total):
            wf_id = self._start_one_workflow(i)
            if wf_id:
                workflow_ids.append(wf_id)

            # Pace submission
            expected_time = start_time + (i + 1) * interval
            sleep_for = expected_time - time.time()
            if sleep_for > 0:
                time.sleep(sleep_for)

            done = len(workflow_ids)
            if done % 100 == 0:
                elapsed = time.time() - start_time
                print(f"  Submitted {done}/{total} ({elapsed:.1f}s)")

        submit_elapsed = time.time() - start_time
        print(f"✓ All {len(workflow_ids)} workflows submitted in {submit_elapsed:.1f}s "
              f"(actual rate: {len(workflow_ids) / submit_elapsed:.1f} wf/s)")

        # Collect results
        queue_times, wf_durations = self._collect_results(workflow_ids)
        elapsed = time.time() - start_time
        _print_latency_report(queue_times, wf_durations, elapsed, len(workflow_ids))

    # ---- duration mode --------------------------------------------------

    def _run_duration_mode(self):
        deadline = time.time() + DURATION_MINUTES * 60
        interval = 1.0 / SUBMIT_RATE
        print(f"\n→ Duration mode: running for {DURATION_MINUTES} min at {SUBMIT_RATE} wf/s")

        all_queue_times = defaultdict(list)
        all_wf_durations = []
        total_started = 0
        report_num = 0
        overall_start = time.time()

        # Submit and collect in rolling windows
        batch_ids = []
        batch_start = time.time()
        BATCH_SIZE = 200  # collect results every N workflows

        while time.time() < deadline:
            wf_id = self._start_one_workflow(total_started)
            if wf_id:
                batch_ids.append(wf_id)
            total_started += 1

            # Pace
            expected_time = batch_start + len(batch_ids) * interval
            sleep_for = expected_time - time.time()
            if sleep_for > 0:
                time.sleep(sleep_for)

            # Collect in batches to avoid unbounded memory
            if len(batch_ids) >= BATCH_SIZE:
                report_num += 1
                queue_times, wf_durations = self._collect_results(batch_ids)
                for ref, times in queue_times.items():
                    all_queue_times[ref].extend(times)
                all_wf_durations.extend(wf_durations)
                remaining = deadline - time.time()
                print(f"  Report #{report_num}: {len(batch_ids)} wf, "
                      f"total={total_started}, remaining={remaining:.0f}s")
                batch_ids = []
                batch_start = time.time()

        # Final batch
        if batch_ids:
            queue_times, wf_durations = self._collect_results(batch_ids)
            for ref, times in queue_times.items():
                all_queue_times[ref].extend(times)
            all_wf_durations.extend(wf_durations)

        elapsed = time.time() - overall_start
        _print_latency_report(dict(all_queue_times), all_wf_durations, elapsed, total_started)

    # ---- helpers --------------------------------------------------------

    def _start_one_workflow(self, index: int) -> str:
        req = StartWorkflowRequest()
        req.name = WORKFLOW_NAME
        req.version = WORKFLOW_VERSION
        req.input = {"run_index": index}
        try:
            return self.workflow_client.start_workflow(start_workflow_request=req)
        except Exception as e:
            logger.error("Failed to start workflow %d: %s", index, e)
            return None

    def _collect_results(self, workflow_ids: list, timeout_s: int = 120) -> tuple:
        """
        Poll completed workflows and extract per-task queue_wait_time.
        Returns (queue_times_by_task_ref, workflow_durations_ms).
        """
        queue_times = defaultdict(list)
        wf_durations = []
        pending = set(workflow_ids)
        deadline = time.time() + timeout_s

        while pending and time.time() < deadline:
            still_pending = set()
            for wf_id in pending:
                try:
                    wf = self.workflow_client.get_workflow(wf_id, include_tasks=True)
                except Exception:
                    still_pending.add(wf_id)
                    continue

                if wf.status not in ("COMPLETED", "FAILED", "TERMINATED", "TIMED_OUT"):
                    still_pending.add(wf_id)
                    continue

                if wf.start_time and wf.end_time:
                    wf_durations.append(wf.end_time - wf.start_time)

                for task in (wf.tasks or []):
                    ref = task.reference_task_name
                    qwt = getattr(task, "queue_wait_time", None)
                    if qwt is not None and qwt >= 0:
                        queue_times[ref].append(qwt)
                    elif (task.scheduled_time and task.start_time
                          and task.start_time >= task.scheduled_time):
                        queue_times[ref].append(task.start_time - task.scheduled_time)

            pending = still_pending
            if pending:
                time.sleep(0.5)

        if pending:
            logger.warning("%d workflows did not complete within timeout", len(pending))

        return dict(queue_times), wf_durations


if __name__ == "__main__":
    unittest.main(verbosity=2)
