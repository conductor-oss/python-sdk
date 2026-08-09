"""
Module-level real openai-agents ``@function_tool`` subjects for FunctionRef
deep-extract tests.

Separate from worker_entry_helpers.py so environments without the
openai-agents extra can still import that module; tests importing THIS
module must be gated with ``pytest.importorskip("agents")``.
"""
import asyncio
import pickle

from agents import function_tool


@function_tool
def oa_get_weather(city: str) -> str:
    """Return a canned weather string for a city."""
    return f"sunny in {city}"


@function_tool
async def oa_get_weather_async(city: str) -> str:
    """Return a canned weather string for a city, asynchronously."""
    return f"async sunny in {city}"


def resolve_and_await_child(ref_bytes: bytes, city: str, q) -> None:
    """Spawn-child target: unpickle a FunctionRef and await its function."""
    ref = pickle.loads(ref_bytes)
    q.put(asyncio.run(ref.resolve()(city)))


def run_weather_entry_child(entry_bytes: bytes, city: str, q) -> None:
    """Spawn-child target: run the sync weather tool as a real task."""
    from conductor.client.http.models import Task

    entry = pickle.loads(entry_bytes)
    task = Task(task_id="t-openai-spawn-1", workflow_instance_id="wf-openai-spawn-1")
    task.input_data = {"city": city}
    task.task_def_name = entry.tool_name
    result = entry(task)
    q.put((str(result.status), dict(result.output_data or {})))
