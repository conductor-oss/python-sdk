"""Regression tests: PLAN_EXECUTE ``planner=`` / ``fallback=`` tools get workers.

Issue #478: tools declared on an agent passed via the ``planner=`` (or
``fallback=``) named slot were never traversed when the runtime collected /
registered worker names.  Because PLAN_EXECUTE stores those agents as separate
attributes (``agent.planner`` / ``agent.fallback``) rather than in
``agent.agents``, a tree walk that only iterated ``agent.agents`` skipped them,
so the planner's tasks stayed SCHEDULED with nothing polling them — the
``86_coding_agent.py`` example hung forever.

These tests are fully deterministic: pure dataclasses and mocks, no LLM, no
live server, no Docker.  They assert only against pre-existing public/private
methods of ``AgentRuntime`` (``_collect_worker_names``, ``_register_workers``,
``_has_worker_tools``, ``_ensure_models_for_agent``), never against helpers
introduced by the fix, so they fail on the original code.
"""

from unittest.mock import MagicMock, patch

import pytest

from conductor.ai.agents import Agent, Strategy
from conductor.ai.agents.runtime.runtime import AgentRuntime
from conductor.ai.agents.tool import get_tool_def, tool


@tool
def planner_only_tool(path: str) -> str:
    """A tool that exists ONLY on the planner slot."""
    return path


@tool
def fallback_only_tool(path: str) -> str:
    """A tool that exists ONLY on the fallback slot."""
    return path


@tool
def harness_tool(path: str) -> str:
    """A tool declared on the parent harness."""
    return path


def _collect_names(agent: Agent) -> set:
    """Call _collect_worker_names without a real server connection."""
    rt = AgentRuntime.__new__(AgentRuntime)
    return rt._collect_worker_names(agent)


class TestPlannerSlotWorkerCollection:
    """_collect_worker_names must walk the planner= / fallback= named slots."""

    def test_planner_tool_is_collected(self):
        planner = Agent(name="planner", model="openai/gpt-4o", tools=[planner_only_tool])
        parent = Agent(
            name="harness",
            model="openai/gpt-4o",
            tools=[harness_tool],
            strategy=Strategy.PLAN_EXECUTE,
            planner=planner,
        )

        names = _collect_names(parent)

        # The parent's own tool is collected...
        assert "harness_tool" in names
        # ...and so is the planner's tool (THE BUG: this was missing).
        assert "planner_only_tool" in names

    def test_fallback_tool_is_collected(self):
        planner = Agent(name="planner", model="openai/gpt-4o", tools=[planner_only_tool])
        fallback = Agent(name="fallback", model="openai/gpt-4o", tools=[fallback_only_tool])
        parent = Agent(
            name="harness",
            model="openai/gpt-4o",
            tools=[harness_tool],
            strategy=Strategy.PLAN_EXECUTE,
            planner=planner,
            fallback=fallback,
        )

        names = _collect_names(parent)

        assert "planner_only_tool" in names
        assert "fallback_only_tool" in names

    def test_planner_system_workers_are_collected(self):
        """System workers on the planner (guardrails) must also be walked."""
        planner = Agent(
            name="planner",
            model="openai/gpt-4o",
            termination=lambda result, iteration: False,
        )
        parent = Agent(
            name="harness",
            model="openai/gpt-4o",
            tools=[harness_tool],
            strategy=Strategy.PLAN_EXECUTE,
            planner=planner,
        )

        names = _collect_names(parent)

        assert "planner_termination" in names


class TestPlannerSlotHasWorkerTools:
    """_has_worker_tools must recurse into planner= / fallback= slots."""

    def test_planner_only_worker_tool_is_detected(self):
        planner = Agent(name="planner", model="openai/gpt-4o", tools=[planner_only_tool])
        parent = Agent(
            name="harness",
            model="openai/gpt-4o",
            tools=[harness_tool],
            strategy=Strategy.PLAN_EXECUTE,
            planner=planner,
        )

        rt = AgentRuntime.__new__(AgentRuntime)

        # Sanity: the parent itself has a worker tool, so it's true regardless.
        assert rt._has_worker_tools(parent) is True
        # The planner slot must independently report True.
        assert rt._has_worker_tools(planner) is True

    def test_planner_slot_detected_when_parent_has_only_server_tools(self):
        """A planner with a worker tool is detected even if the parent's own
        tools are server-side (http) and need no local worker."""
        from conductor.ai.agents.tool import http_tool

        parent_http = http_tool(name="fetch", description="d", url="http://example.test")
        planner = Agent(name="planner", model="openai/gpt-4o", tools=[planner_only_tool])
        parent = Agent(
            name="harness",
            model="openai/gpt-4o",
            tools=[parent_http],
            strategy=Strategy.PLAN_EXECUTE,
            planner=planner,
        )

        rt = AgentRuntime.__new__(AgentRuntime)

        # Parent alone has no worker tools; True only because of the planner slot.
        assert rt._has_worker_tools(parent) is True


class TestPlannerSlotRegistration:
    """_register_workers must register the planner's tool workers."""

    def test_planner_tool_worker_registered(self):
        planner = Agent(name="planner", model="openai/gpt-4o", tools=[planner_only_tool])
        parent = Agent(
            name="harness",
            model="openai/gpt-4o",
            tools=[harness_tool],
            strategy=Strategy.PLAN_EXECUTE,
            planner=planner,
        )

        rt = AgentRuntime.__new__(AgentRuntime)
        registered: list = []

        def _fake_register_tool_workers(tools, agent_name, **kwargs):
            for t in tools:
                registered.append((agent_name, get_tool_def(t).name))

        with patch(
            "conductor.ai.agents.runtime.tool_registry.ToolRegistry.register_tool_workers",
            side_effect=_fake_register_tool_workers,
        ):
            rt._register_workers(parent, required_workers=None, domain=None)

        registered_names = {name for _, name in registered}
        assert "harness_tool" in registered_names
        # THE BUG: the planner's tool worker was never registered.
        assert "planner_only_tool" in registered_names

    def test_fallback_tool_worker_registered(self):
        planner = Agent(name="planner", model="openai/gpt-4o", tools=[planner_only_tool])
        fallback = Agent(name="fallback", model="openai/gpt-4o", tools=[fallback_only_tool])
        parent = Agent(
            name="harness",
            model="openai/gpt-4o",
            tools=[harness_tool],
            strategy=Strategy.PLAN_EXECUTE,
            planner=planner,
            fallback=fallback,
        )

        rt = AgentRuntime.__new__(AgentRuntime)
        registered: list = []

        def _fake_register_tool_workers(tools, agent_name, **kwargs):
            for t in tools:
                registered.append((agent_name, get_tool_def(t).name))

        with patch(
            "conductor.ai.agents.runtime.tool_registry.ToolRegistry.register_tool_workers",
            side_effect=_fake_register_tool_workers,
        ):
            rt._register_workers(parent, required_workers=None, domain=None)

        registered_names = {name for _, name in registered}
        assert "planner_only_tool" in registered_names
        assert "fallback_only_tool" in registered_names


class TestPlannerSlotModelEnsuring:
    """_ensure_models_for_agent must walk planner= / fallback= slots."""

    def _make_runtime(self):
        with (
            patch("conductor.client.orkes_clients.OrkesClients") as MockClients,
            patch("conductor.ai.agents.runtime.worker_manager.TaskHandler", create=True),
        ):
            mock_clients = MagicMock()
            MockClients.return_value = mock_clients
            mock_clients.get_integration_client.return_value = MagicMock()

            from conductor.ai.agents.runtime.config import AgentConfig

            runtime = AgentRuntime(
                settings=AgentConfig(auto_register_integrations=True)
            )
            return runtime

    def test_planner_model_is_ensured(self):
        planner = Agent(name="planner", model="anthropic/claude-sonnet-4-20250514")
        parent = Agent(
            name="harness",
            model="openai/gpt-4o",
            tools=[harness_tool],
            strategy=Strategy.PLAN_EXECUTE,
            planner=planner,
        )

        runtime = self._make_runtime()
        with patch.object(runtime, "_ensure_model") as mock_ensure:
            runtime._ensure_models_for_agent(parent)

        ensured = {c.args[0] for c in mock_ensure.call_args_list}
        assert "openai/gpt-4o" in ensured
        # THE BUG: the planner's model was never ensured.
        assert "anthropic/claude-sonnet-4-20250514" in ensured
