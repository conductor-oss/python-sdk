"""
Spawn start-method safety tests for Worker / @worker_task (issues #264, #271).

Before the fix, Worker instances built from @worker_task functions could not
be pickled, so TaskHandler could not start worker subprocesses under the
'spawn' multiprocessing start method (the only safe method on macOS, and the
SDK default):

    TypeError: cannot pickle '_thread.lock' object                (Worker/ApiClient locks)
    PicklingError: it's not the same object as module.name        (decorator rebinding)

...and on failure the parent process hung forever instead of exiting.
"""
import inspect
import multiprocessing
import pickle
import unittest

import conductor.client.automator.task_handler as task_handler
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.worker import (
    Worker,
    _ExecuteFunctionReference,
    _importable_function_reference,
)
from conductor.client.worker.worker_task import worker_task

from tests.unit.resources import spawn_worker_helpers as helpers

# Importing the helpers module registered its @worker_task functions in the
# global registry. Scrub them immediately so tests that scan for annotated
# workers (scan_for_annotated_workers=True) are not polluted.
for _key in [k for k in list(task_handler._decorated_functions) if k[0].startswith("spawn_pickle_")]:
    task_handler._decorated_functions.pop(_key, None)


def _make_decorated_worker() -> Worker:
    """Build a Worker exactly as TaskHandler does for a @worker_task function:
    from the ORIGINAL (pre-wrapper) function object."""
    return Worker(
        task_definition_name="spawn_pickle_task",
        execute_function=inspect.unwrap(helpers.spawn_pickle_task),
        domain="spawn-test",
        thread_count=2,
        poll_interval=250,
    )


def _make_task(x: int = 21) -> Task:
    return Task(
        task_id="task-id-1",
        workflow_instance_id="wf-id-1",
        task_def_name="spawn_pickle_task",
        input_data={"x": x},
        status="IN_PROGRESS",
    )


class TestWorkerPickleRoundTrip(unittest.TestCase):
    def test_decorated_worker_pickle_roundtrip_restores_original_function(self):
        worker = _make_decorated_worker()
        restored = pickle.loads(pickle.dumps(worker))

        # Same function object: resolved via module reference + __wrapped__.
        self.assertIs(restored.execute_function, worker.execute_function)
        self.assertEqual(restored.get_task_definition_name(), "spawn_pickle_task")
        self.assertEqual(restored.domain, "spawn-test")
        self.assertEqual(restored.thread_count, 2)
        self.assertEqual(restored.poll_interval, 250)

    def test_unpickled_worker_executes_task(self):
        restored = pickle.loads(pickle.dumps(_make_decorated_worker()))
        result = restored.execute(_make_task(x=21))
        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data, {"doubled": 42})

    def test_async_decorated_worker_preserves_coroutine_detection(self):
        worker = Worker(
            task_definition_name="spawn_pickle_async_task",
            execute_function=inspect.unwrap(helpers.spawn_pickle_async_task),
        )
        restored = pickle.loads(pickle.dumps(worker))
        # TaskHandler routes to AsyncTaskRunner based on this check.
        self.assertTrue(inspect.iscoroutinefunction(restored.execute_function))

    def test_plain_function_worker_pickles_by_reference(self):
        worker = Worker(
            task_definition_name="plain_task",
            execute_function=helpers.plain_function_worker,
        )
        restored = pickle.loads(pickle.dumps(worker))
        self.assertIs(restored.execute_function, helpers.plain_function_worker)

    def test_nested_decorated_function_fails_fast_in_parent(self):
        """A @worker_task function defined inside another function can never be
        re-imported by a spawn child; pickling must fail in the PARENT (clear,
        immediate) rather than crash-looping the child at unpickle time."""

        @worker_task(task_definition_name="nested_probe")
        def nested_probe(x: int) -> int:
            return x

        # Scrub the registration side effect of the local decorator above.
        task_handler._decorated_functions.pop(("nested_probe", None), None)

        worker = Worker(
            task_definition_name="nested_probe",
            execute_function=inspect.unwrap(nested_probe),
        )
        # PicklingError or AttributeError depending on Python version; both
        # are caught by TaskHandler.start_processes' actionable error handler.
        with self.assertRaises((pickle.PicklingError, AttributeError)):
            pickle.dumps(worker)


class TestWorkerRuntimeStateIsolation(unittest.TestCase):
    def test_api_client_is_lazy_and_never_pickled(self):
        worker = _make_decorated_worker()
        self.assertIsNone(worker._api_client)  # not built in the parent

        restored = pickle.loads(pickle.dumps(worker))
        self.assertIsNone(restored._api_client)  # not built by unpickling

        # Property builds it on first use; setter allows injection.
        sentinel = object()
        restored.api_client = sentinel
        self.assertIs(restored.api_client, sentinel)

    def test_lock_and_async_state_rebuilt_fresh_in_child(self):
        worker = _make_decorated_worker()
        worker._pending_async_tasks["stale-task-id"] = object()

        restored = pickle.loads(pickle.dumps(worker))

        self.assertIsNotNone(restored._pending_tasks_lock)
        self.assertIsNot(restored._pending_tasks_lock, worker._pending_tasks_lock)
        self.assertEqual(restored._pending_async_tasks, {})
        self.assertIsNone(restored._background_loop)
        # Lock must be functional.
        with restored._pending_tasks_lock:
            pass

    def test_original_worker_unaffected_by_pickling(self):
        worker = _make_decorated_worker()
        pickle.dumps(worker)
        result = worker.execute(_make_task(x=5))
        self.assertEqual(result.output_data, {"doubled": 10})


class TestExecuteFunctionReference(unittest.TestCase):
    def test_reference_created_for_decorator_rebound_function(self):
        original = inspect.unwrap(helpers.spawn_pickle_task)
        ref = _importable_function_reference(original)
        self.assertIsInstance(ref, _ExecuteFunctionReference)
        self.assertIs(ref.resolve(), original)

    def test_no_reference_for_plain_module_function(self):
        self.assertIsNone(_importable_function_reference(helpers.plain_function_worker))

    def test_no_reference_for_lambda_nested_or_non_function(self):
        self.assertIsNone(_importable_function_reference(lambda x: x))
        self.assertIsNone(_importable_function_reference("not-a-function"))
        self.assertIsNone(_importable_function_reference(None))

        def local_fn(x):
            return x

        self.assertIsNone(_importable_function_reference(local_fn))


class TestWorkerInRealSpawnChild(unittest.TestCase):
    """The definitive regression test: transfer a @worker_task Worker into a
    real 'spawn' child process (fresh interpreter, re-imports modules) and
    execute a task there. This is exactly what TaskHandler does when
    CONDUCTOR_MP_START_METHOD=spawn (default), and exactly what failed in
    issues #264/#271."""

    def test_worker_executes_in_spawn_child_process(self):
        ctx = multiprocessing.get_context("spawn")
        result_queue = ctx.Queue()
        process = ctx.Process(
            target=helpers.run_worker_in_child,
            args=(_make_decorated_worker(), result_queue),
        )
        process.start()
        try:
            status, output = result_queue.get(timeout=60)
        finally:
            process.join(timeout=10)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)

        self.assertEqual(process.exitcode, 0)
        self.assertEqual(status, "COMPLETED")
        self.assertEqual(output, {"doubled": 42})


if __name__ == "__main__":
    unittest.main()
