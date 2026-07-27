"""
Module-level real openai-agents ``@function_tool`` subjects for FunctionRef
deep-extract tests.

Separate from worker_entry_helpers.py so environments without the
openai-agents extra can still import that module; tests importing THIS
module must be gated with ``pytest.importorskip("agents")``.
"""
from agents import function_tool


@function_tool
def oa_get_weather(city: str) -> str:
    """Return a canned weather string for a city."""
    return f"sunny in {city}"


@function_tool
async def oa_get_weather_async(city: str) -> str:
    """Return a canned weather string for a city, asynchronously."""
    return f"async sunny in {city}"
