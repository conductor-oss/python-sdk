"""Regression tests for examples 63b/63d: serve the workers that 63c/63e need.

Issue #487: ``63c_run_by_name.py`` and ``63e_run_monitoring.py`` execute a
pre-deployed agent *by name* (``runtime.run("doc_assistant", ...)`` /
``runtime.run("monitoring", ...)``).  A run-by-name client never sees the
agent object, so it cannot start the agent's tool workers.  Some other
process must be serving them.  ``63b_serve.py`` and ``63d_serve_from_package.py``
are the examples meant to be that process, but their executable bodies called
``runtime.run(<agent object>, ...)`` instead of ``runtime.serve(...)`` — so no
shipped example ever served workers and the run-by-name clients hung forever.

These tests pin the example *executable bodies* (the ``__main__`` block) to the
serving behaviour, using only the stdlib ``ast`` module so they fail on the
original, un-fixed examples.  They do not import the examples (which would
execute their module-level code and require a live server).
"""

from __future__ import annotations

import ast
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parents[3] / "examples" / "agents"


def _main_block_calls(path: Path) -> list[ast.Call]:
    """Return every ``runtime.<method>(...)`` call inside the ``__main__`` block.

    Only calls whose receiver is the ``AgentRuntime`` context-manager binding
    (``with AgentRuntime() as runtime:``) are returned, so module-level helper
    calls in the example are ignored.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))

    main_body: list[ast.stmt] = []
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        # ``if __name__ == "__main__":``
        if (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
            and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value == "__main__"
        ):
            main_body = node.body
            break

    runtime_names: set[str] = set()
    for node in ast.walk(ast.Module(body=main_body, type_ignores=[])):
        if isinstance(node, ast.With):
            for item in node.items:
                ctx = item.context_expr
                if (
                    isinstance(ctx, ast.Call)
                    and isinstance(ctx.func, ast.Name)
                    and ctx.func.id == "AgentRuntime"
                    and isinstance(item.optional_vars, ast.Name)
                ):
                    runtime_names.add(item.optional_vars.id)

    calls: list[ast.Call] = []
    for node in ast.walk(ast.Module(body=main_body, type_ignores=[])):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in runtime_names
        ):
            calls.append(node)
    return calls


def _method_name(call: ast.Call) -> str:
    assert isinstance(call.func, ast.Attribute)
    return call.func.attr


def _positional_names(call: ast.Call) -> list[str]:
    return [a.id for a in call.args if isinstance(a, ast.Name)]


def test_63b_serves_doc_assistant_and_ops_bot():
    calls = _main_block_calls(EXAMPLES / "63b_serve.py")
    serve_calls = [c for c in calls if _method_name(c) == "serve"]
    assert serve_calls, (
        "63b_serve.py must call runtime.serve(...) in its __main__ block so a "
        "process serves the workers that 63c_run_by_name.py needs; it currently "
        "does not serve any agent."
    )
    served = set()
    for call in serve_calls:
        served.update(_positional_names(call))
    assert {"doc_assistant", "ops_bot"} <= served, (
        f"63b must serve both agents by name so 63c can run 'doc_assistant'; "
        f"got served={sorted(served)}"
    )


def test_63b_does_not_run_an_agent_object():
    calls = _main_block_calls(EXAMPLES / "63b_serve.py")
    run_calls = [c for c in calls if _method_name(c) == "run"]
    assert not run_calls, (
        "63b_serve.py is the serving daemon for 63c; its __main__ block must "
        "not execute an agent with runtime.run(<agent>, ...)."
    )


def test_63d_serves_monitoring_agent():
    calls = _main_block_calls(EXAMPLES / "63d_serve_from_package.py")
    serve_calls = [c for c in calls if _method_name(c) == "serve"]
    assert serve_calls, (
        "63d_serve_from_package.py must call runtime.serve(...) in its __main__ "
        "block so a process serves the workers that 63e_run_monitoring.py needs; "
        "it currently does not serve any agent."
    )
    served = set()
    for call in serve_calls:
        served.update(_positional_names(call))
    assert "monitoring_agent" in served, (
        f"63d must serve the monitoring agent so 63e can run 'monitoring'; "
        f"got served={sorted(served)}"
    )


def test_63d_does_not_run_an_agent_object():
    calls = _main_block_calls(EXAMPLES / "63d_serve_from_package.py")
    run_calls = [c for c in calls if _method_name(c) == "run"]
    assert not run_calls, (
        "63d_serve_from_package.py is the serving daemon for 63e; its __main__ "
        "block must not execute an agent with runtime.run(<agent>, ...)."
    )
