"""
Module-level helpers for FunctionRef / spawn-safety entry tests.

These MUST live in an importable module (not a test function's local scope):
the 'spawn' start method pickles by reference, and the child process
re-imports this module to resolve them. Same rationale as
spawn_worker_helpers.py (idea-2's spawn regression tests).
"""
import pickle

from conductor.ai.agents.tool import tool


def plain_sample(x: int) -> int:
    """Module-level plain function — FunctionRef depth 0."""
    return x * 2


@tool
def decorated_sample(x: int) -> int:
    """@tool-decorated: module global is the wraps-wrapper, ToolDef.func the original."""
    return x + 7


async def async_sample(x: int) -> int:
    """Module-level async function for async-entry round-trips."""
    return x * 3


class AsyncCallEntry:
    """Callable instance with async __call__ — async-detection test subject."""

    def __init__(self, offset: int = 0):
        self.offset = offset

    async def __call__(self, x: int) -> int:
        return x + self.offset


class SyncCallEntry:
    """Callable instance with sync __call__ and picklable attrs."""

    def __init__(self, factor: int = 1):
        self.factor = factor

    def __call__(self, x: int) -> int:
        return x * self.factor


def resolve_and_call_child(ref_bytes: bytes, arg: int, q) -> None:
    """Spawn-child target: unpickle a FunctionRef, resolve it, call it."""
    ref = pickle.loads(ref_bytes)
    fn = ref.resolve()
    q.put(fn(arg))


def run_code_entry_child(entry_bytes: bytes, code: str, q) -> None:
    """Spawn-child target: unpickle a CodeExecutionEntry and execute code."""
    entry = pickle.loads(entry_bytes)
    q.put(entry(code))


def run_tool_entry_child(entry_bytes: bytes, x: int, q) -> None:
    """Spawn-child target: unpickle a ToolWorkerEntry and execute a real Task.

    Proves the whole worker unit crosses the boundary and executes without any
    parent-populated registry state (the child imports everything fresh).
    """
    from conductor.client.http.models import Task

    entry = pickle.loads(entry_bytes)
    task = Task(task_id="t-spawn-1", workflow_instance_id="wf-spawn-1")
    task.input_data = {"x": x}
    task.task_def_name = entry.tool_name
    result = entry(task)
    q.put((str(result.status), dict(result.output_data or {})))
