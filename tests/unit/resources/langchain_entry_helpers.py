"""
Module-level langchain ``@tool`` subjects for FunctionRef container-hop tests.

Separate from worker_entry_helpers.py so environments without langchain can
still import that module; tests importing THIS module must be gated with
``pytest.importorskip("langchain_core")``.
"""
from langchain_core.tools import tool as lc_tool


@lc_tool
def lc_multiply(a: int, b: int) -> str:
    """Multiply two numbers and return the product."""
    return str(a * b)


@lc_tool
async def lc_multiply_async(a: int, b: int) -> str:
    """Multiply two numbers asynchronously and return the product."""
    return str(a * b)
