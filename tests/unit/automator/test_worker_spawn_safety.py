import pickle
import unittest

import conductor.client.automator.task_handler as task_handler
from conductor.client.worker.worker import Worker
from conductor.client.worker.worker_task import worker_task

_TASK_NAME = "spawn_safety_probe"


class TestWorkerSpawnSafety(unittest.TestCase):
    """Reproduces the macOS fork/spawn bug for @worker_task workers.

    On macOS the multiprocessing 'fork' start method is unsafe, and the
    documented escape hatch (CONDUCTOR_MP_START_METHOD=spawn) requires every
    Process argument to be picklable. The Worker built by @worker_task held a
    live ApiClient (whose connection pool owns a _thread.lock) and a
    threading.Lock, so pickling it failed with:

        TypeError: cannot pickle '_thread.lock' object

    and its execute_function (a wrapper-shadowed function) could not be pickled
    by reference either. This test fails before the spawn-safety fix and passes
    after it.
    """

    def setUp(self) -> None:
        # Hermetic registry: some other tests replace _decorated_functions with a
        # Mock and don't restore it. Swap in a fresh dict and restore in tearDown.
        self._saved_registry = task_handler._decorated_functions
        task_handler._decorated_functions = {}

    def tearDown(self) -> None:
        task_handler._decorated_functions = self._saved_registry

    def test_worker_task_worker_is_picklable_for_spawn(self):
        # Register a decorated worker fresh (other tests clear the registry).
        @worker_task(task_definition_name=_TASK_NAME)
        def spawn_safety_probe(x: int) -> int:
            return x + 1

        # Build the Worker exactly as the SDK does for a decorated function,
        # straight from the registry record (avoids helpers other tests mock).
        record = task_handler._decorated_functions[(_TASK_NAME, None)]
        worker = Worker(
            task_definition_name=_TASK_NAME,
            execute_function=record["func"],
        )

        restored = pickle.loads(pickle.dumps(worker))

        self.assertEqual(restored.get_task_definition_name(), _TASK_NAME)
        self.assertEqual(restored.execute_function(1), 2)


if __name__ == "__main__":
    unittest.main()
