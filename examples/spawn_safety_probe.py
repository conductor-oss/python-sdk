"""
spawn_safety_probe.py - @worker_task spawn-safety probe (GitHub issues #264/#271).

Run from the repo root:
    PYTHONPATH=src python3 examples/spawn_safety_probe.py

Forces the 'spawn' multiprocessing start method (the SDK default; also the
only safe method on macOS) and then checks, in order:

  1. Which Worker attributes survive pickling (attribute-level diagnostic)
  2. Whole-Worker pickle round-trip + task execution on the restored worker
  3. Worker transferred into a REAL 'spawn' child process and executed there
     (exactly what TaskHandler.start_processes() does)

Broken SDK output:  FAIL lines for api_client / _pending_tasks_lock /
                    _execute_function; round-trip and spawn-child checks fail.
Fixed SDK output:   everything PASS.
"""
import os
import sys

# Force spawn BEFORE importing any conductor module: task_handler pins the
# start method at import time from this env var.
os.environ["CONDUCTOR_MP_START_METHOD"] = "spawn"

import multiprocessing
import pickle

from conductor.client.worker.worker_task import worker_task
from conductor.client.http.models.task import Task


@worker_task(task_definition_name="pickle_probe_task")
def pickle_probe_task(x: int) -> dict:
    return {"doubled": x * 2}


def _make_task() -> Task:
    return Task(
        task_id="probe-task-id",
        workflow_instance_id="probe-wf-id",
        task_def_name="pickle_probe_task",
        input_data={"x": 21},
        status="IN_PROGRESS",
    )


def run_in_child(worker, result_queue) -> None:
    """Spawn-child entry point: unpickling `worker` here IS the test."""
    result = worker.execute(_make_task())
    result_queue.put((str(result.status), result.output_data))


def get_probe_worker():
    from conductor.client.automator.task_handler import get_registered_workers
    return next(w for w in get_registered_workers()
                if w.task_definition_name == "pickle_probe_task")


def main() -> int:
    failures = 0
    print(f"python={sys.version.split()[0]}  platform={sys.platform}")

    worker = get_probe_worker()  # importing task_handler pins the start method
    print(f"multiprocessing start method: {multiprocessing.get_start_method(allow_none=True)}\n")

    # -- 1. attribute-level diagnostic --------------------------------------
    # Pickle what pickling actually serializes: the __getstate__ output.
    # (Raw __dict__ values legitimately contain process-local objects - a
    # threading.Lock, the original decorated function - which __getstate__
    # excludes or substitutes. If a future change adds unpicklable state and
    # forgets to handle it in __getstate__, this section catches it.)
    print("[1] Worker pickled-state (__getstate__) picklability:")
    state = worker.__getstate__() if hasattr(worker, "__getstate__") else dict(worker.__dict__)
    for k, v in state.items():
        try:
            pickle.dumps(v)
            print(f"    PASS  {k}")
        except Exception as e:
            failures += 1
            print(f"    FAIL  {k}: {type(e).__name__}: {str(e)[:70]}")

    # -- 2. whole-worker round-trip + execute --------------------------------
    print("\n[2] Whole-Worker pickle round-trip:")
    try:
        restored = pickle.loads(pickle.dumps(worker))
        same_fn = restored.execute_function is worker.execute_function
        result = restored.execute(_make_task())
        if str(result.status) == "COMPLETED" and result.output_data == {"doubled": 42}:
            print(f"    PASS  round-trip (same function object: {same_fn}, "
                  f"result: {result.output_data})")
        else:
            failures += 1
            print(f"    FAIL  unexpected result: {result.status} {result.output_data}")
    except Exception as e:
        failures += 1
        print(f"    FAIL  {type(e).__name__}: {str(e)[:100]}")

    # -- 3. real spawn child --------------------------------------------------
    print("\n[3] Execute in a real 'spawn' child process:")
    ctx = multiprocessing.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=run_in_child, args=(get_probe_worker(), q))
    try:
        p.start()
        status, output = q.get(timeout=60)
        p.join(timeout=10)
        if status == "COMPLETED" and output == {"doubled": 42}:
            print(f"    PASS  child exitcode={p.exitcode}, result={output}")
        else:
            failures += 1
            print(f"    FAIL  status={status} output={output}")
    except Exception as e:
        failures += 1
        print(f"    FAIL  {type(e).__name__}: {str(e)[:100]}")
        if p.is_alive():
            p.terminate()
            p.join(timeout=5)

    print(f"\n{'ALL CHECKS PASSED' if failures == 0 else f'{failures} CHECK(S) FAILED'}")
    return 0 if failures else 1


if __name__ == "__main__":
    sys.exit(main())
