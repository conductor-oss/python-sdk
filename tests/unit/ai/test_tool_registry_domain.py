"""Tests for ToolRegistry.register_tool_workers domain propagation.

A nested sub-agent (e.g. a SWARM member) is never itself marked
`stateful=True` — only the top-level orchestrator carries that flag, even
though the whole compiled graph (including the sub-agent's own tools) is
domain-routed once any agent in the tree is stateful. `domain` is already
resolved once, tree-wide, by `AgentRuntime._resolve_worker_domain` /
`_has_stateful_tools` before `register_tool_workers` is ever called, so it
must be applied whenever non-None — regardless of the immediate agent's own
`.stateful` attribute. Re-deriving statefulness locally left a SWARM
member's own tool worker polling the domain-less queue while its task sat in
the domain-scoped queue forever (conductor-oss #1363 follow-up).
"""

from unittest.mock import patch

from conductor.ai.agents.runtime.tool_registry import ToolRegistry
from conductor.ai.agents.tool import tool


@tool
def swarm_tool(task: str) -> str:
    """Perform a task."""
    return f"done:{task}"


def _register_and_capture_domain(domain):
    captured = {}

    def fake_worker_task(**kwargs):
        def _decorator(fn):
            captured["domain"] = kwargs.get("domain")
            return fn

        return _decorator

    with patch(
        "conductor.client.worker.worker_task.worker_task",
        side_effect=fake_worker_task,
    ):
        ToolRegistry().register_tool_workers([swarm_tool], "swarm_agent_a", domain=domain)

    return captured


class TestRegisterToolWorkersDomain:
    def test_domain_applied_regardless_of_agent_or_tool_stateful_flag(self):
        captured = _register_and_capture_domain(domain="abc123")
        assert captured["domain"] == "abc123"

    def test_domain_none_stays_none(self):
        captured = _register_and_capture_domain(domain=None)
        assert captured["domain"] is None
