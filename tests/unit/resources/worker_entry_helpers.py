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
