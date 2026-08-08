"""Regression e2e for ADK's ``mode="single_turn"`` agent-as-tool pattern.

An ADK "agent-as-tool" coordinator (a root ``Agent`` whose ``sub_agents`` each
declare ``mode="single_turn"``) hangs permanently on Conductor: status stays
``RUNNING``, no error, no timeout, no answer. The identical agent runs
correctly under local ``adk web`` / ``adk run``.

Why it breaks
-------------
google-adk (>= 2.1.0) itself materialises a ``_SingleTurnAgentTool`` into the
*parent's* ``tools`` list for every single-turn sub-agent, while still listing
that agent under ``sub_agents``. ADK reconciles the duplication at request time
(``_get_transfer_targets()`` excludes single-turn agents from transfer); the
server compiles from the serialised snapshot instead, so both survive. It
therefore sees a coordinator with tools AND sub-agents, dispatches to the
hybrid compiler, and offers the LLM *two* tools per sub-agent:

1. the bare sub-agent name — routed to ``FORK_JOIN_DYNAMIC``, which forks a
   SIMPLE task typed with the sub-agent's own name. No worker is ever
   registered for it (the SDK only registers the leaf ``@tool`` functions
   nested inside each sub-agent), so the task sits SCHEDULED and the JOIN
   stays IN_PROGRESS forever; and
2. ``<coordinator>_transfer_to_<sub>`` — a compiler-owned control signal that
   terminates the loop and hands off permanently to exactly one sub-agent.

Both are wrong, which is what makes this deterministic to test even though the
LLM's choice between them is a coin flip:

* path 1 → never completes                → caught by the status assertion
* path 2 → completes with a *partial* answer, because a permanent transfer can
  only ever surface one specialist (and that specialist is handed the verbatim
  user prompt) → caught by the content assertion

A correct implementation offers exactly one callable path per single-turn
sub-agent, wired to a real executor, and lets the coordinator call both and
combine the results — which is precisely what its instruction asks for.

Run::

    pytest e2e/test_adk_single_turn_agent_tool.py -v -s

Requirements:
    - Conductor server running (CONDUCTOR_SERVER_URL, default
      http://localhost:8080/api)
    - CONDUCTOR_AGENT_LLM_MODEL provider key configured *on the server*
    - google-adk installed (test skips otherwise)
"""

import uuid
from typing import Any, Dict, Iterator, List

import pytest

pytestmark = [
    pytest.mark.e2e,
]

adk_agents = pytest.importorskip(
    "google.adk.agents", reason="google-adk not installed"
)
Agent = adk_agents.Agent

TIMEOUT = 300  # 5 min per run — CI runners are slower
RUNS = 3  # the buggy tool choice is nondeterministic — sample it

# Unique per session so repeated local runs never collide with a stale
# registered definition of the same agent name.
SUFFIX = uuid.uuid4().hex[:8]
WEATHER_AGENT = f"e2e_adk_st_weather_{SUFFIX}"
TIME_AGENT = f"e2e_adk_st_time_{SUFFIX}"
COORDINATOR = f"e2e_adk_st_coordinator_{SUFFIX}"

# Deterministic tool payloads. The LLM is live (no mocks, per suite
# convention), but the tools are not — these sentinels let the content
# assertion name exactly which specialist did or did not contribute.
TEMP_SENTINEL = "11.5"
TIME_SENTINEL = "14:37"

PROMPT = "What is the time and weather in Seattle?"


# ===================================================================
# The reported agent shape
# ===================================================================


def get_weather(city: str) -> str:
    """Get the current temperature, wind speed, and humidity for a city."""
    return f"{city}: {TEMP_SENTINEL}°C, wind 8 km/h, humidity 72%"


def get_current_time_by_city(city_name: str) -> str:
    """Finds the current local time for a given city name."""
    return f"The current local time in {city_name} is {TIME_SENTINEL}."


def _build_coordinator(model: str) -> Any:
    """Coordinator with two ``mode="single_turn"`` sub-agents."""
    weather_specialist = Agent(
        name=WEATHER_AGENT,
        model=model,
        description="Handles questions about current weather conditions in a city.",
        instruction=(
            "You answer questions about the weather in a city using your "
            "get_weather tool. Only handle weather questions."
        ),
        tools=[get_weather],
        mode="single_turn",
    )

    time_specialist = Agent(
        name=TIME_AGENT,
        model=model,
        description="Handles questions about the current local time in a city.",
        instruction=(
            "You answer questions about the current local time in a city using "
            "your get_current_time_by_city tool. Only handle time questions."
        ),
        tools=[get_current_time_by_city],
        mode="single_turn",
    )

    return Agent(
        name=COORDINATOR,
        model=model,
        description=(
            "Coordinates weather and time questions by calling specialist "
            "sub-agents as tools."
        ),
        instruction=(
            f"You are a coordinator. Call '{WEATHER_AGENT}' for weather questions "
            f"and '{TIME_AGENT}' for time questions. If a request needs both, call "
            "both, then combine their results into one final answer yourself."
        ),
        sub_agents=[weather_specialist, time_specialist],
    )


# ===================================================================
# Helpers
# ===================================================================


def _walk_tasks(tasks: Any) -> Iterator[Dict[str, Any]]:
    """Yield every task in a workflow def, descending into all nesting."""
    if not tasks:
        return
    for task in tasks:
        if not isinstance(task, dict):
            continue
        yield task
        yield from _walk_tasks(task.get("loopOver"))
        yield from _walk_tasks(task.get("defaultCase"))
        for branch in task.get("forkTasks") or []:
            yield from _walk_tasks(branch)
        for case_tasks in (task.get("decisionCases") or {}).values():
            yield from _walk_tasks(case_tasks)
        sub = (task.get("subWorkflowParam") or {}).get("workflowDefinition")
        if isinstance(sub, dict):
            yield from _walk_tasks(sub.get("tasks"))


def _coordinator_tool_names(workflow_def: Dict[str, Any]) -> List[str]:
    """Every tool name offered to the coordinator's own LLM task.

    Scoped by task-reference prefix so a sub-agent's inlined SUB_WORKFLOW
    definition — which legitimately offers ``get_weather`` and friends —
    cannot contaminate the coordinator's tool list.
    """
    names: List[str] = []
    for task in _walk_tasks(workflow_def.get("tasks")):
        if task.get("type") != "LLM_CHAT_COMPLETE":
            continue
        if not task.get("taskReferenceName", "").startswith(COORDINATOR):
            continue
        for spec in task.get("inputParameters", {}).get("tools") or []:
            if not isinstance(spec, dict):
                continue
            fn = spec.get("function")
            name = fn.get("name") if isinstance(fn, dict) else spec.get("name")
            if name:
                names.append(str(name))
    return names


def _run_diagnostic(result) -> str:
    """Build a diagnostic string from a run result for error messages."""
    parts = [f"status={result.status}", f"execution_id={result.execution_id}"]
    output = result.output
    if isinstance(output, dict):
        parts.append(f"output_keys={list(output.keys())}")
        if "finishReason" in output:
            parts.append(f"finishReason={output['finishReason']}")
    if getattr(result, "tool_calls", None):
        parts.append(
            f"tool_calls={[tc.get('name', '') for tc in result.tool_calls]}"
        )
    return " | ".join(parts)


def _output_text(result) -> str:
    """Flatten a run result's output to searchable text."""
    output = result.output
    if output is None:
        return ""
    if isinstance(output, dict):
        return str(output)
    return str(output)


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture(scope="module")
def compiled_plan(runtime, model):
    """Compile the coordinator without executing it.

    ``plan()`` round-trips the serialised ADK config through the server's
    compiler and returns ``{workflowDef, requiredWorkers}`` — no workflow is
    started, no LLM is called, so this half of the regression is fully
    deterministic.
    """
    return runtime.plan(_build_coordinator(model))


@pytest.fixture(scope="module")
def single_turn_runs(runtime, model):
    """Execute the coordinator RUNS times and collect every result."""
    coordinator = _build_coordinator(model)
    results = []
    for i in range(RUNS):
        result = runtime.run(coordinator, PROMPT, timeout=TIMEOUT)
        print(
            f"  Run {i + 1}/{RUNS}: status={result.status} "
            f"wf={result.execution_id}"
        )
        results.append(result)
    return results


# ===================================================================
# Tests
# ===================================================================


@pytest.mark.timeout(1800)  # 30 min — three live multi-agent runs
class TestAdkSingleTurnAgentTool:
    def test_one_callable_path_per_single_turn_subagent(self, compiled_plan):
        """Each single-turn sub-agent is reachable exactly one way.

        The deterministic half of the regression — no dependency on what the
        LLM chooses. Pre-fix the coordinator is offered both the bare
        sub-agent name and ``<coordinator>_transfer_to_<sub>``, i.e. two tools
        with incompatible semantics for one capability, only one of which has
        an executor at all.
        """
        workflow_def = compiled_plan.get("workflowDef")
        assert workflow_def, (
            f"plan() returned no workflowDef. Keys: {list(compiled_plan.keys())}"
        )

        tool_names = _coordinator_tool_names(workflow_def)
        print(f"  coordinator tools: {tool_names}")
        print(f"  requiredWorkers: {compiled_plan.get('requiredWorkers')}")
        assert tool_names, (
            "coordinator LLM task offered no tools — the compiled shape is not "
            "what this test assumes; inspect workflowDef before trusting the "
            "assertions below."
        )

        for sub_agent in (WEATHER_AGENT, TIME_AGENT):
            paths = [n for n in tool_names if sub_agent.lower() in n.lower()]
            assert len(paths) == 1, (
                f"'{sub_agent}' is reachable via {len(paths)} tools {paths}; a "
                f"single-turn sub-agent must have exactly one callable path. "
                f"Two means the bare-name FORK_JOIN_DYNAMIC route and the "
                f"transfer control signal are both live. "
                f"All coordinator tools: {tool_names}"
            )

    def test_server_requires_no_worker_the_sdk_cannot_supply(
        self, compiled_plan, model
    ):
        """Every ``requiredWorker`` must be one the SDK can actually register.

        The compile response tells the client which workers to stand up. For
        this agent the server asks for the two single-turn sub-agent names on
        top of the two leaf ``@tool`` functions — but the SDK only ever
        extracts workers for the leaf callables, so two of the four are never
        supplied. Neither side reports the mismatch; the forked task simply
        sits SCHEDULED forever.

        Deliberately fix-agnostic: it does not care *how* a single-turn
        sub-agent is executed (SUB_WORKFLOW, a real worker, anything else),
        only that the server never demands a worker the client cannot give it.
        """
        from conductor.ai.agents.frameworks.serializer import serialize_agent

        # An empty requiredWorkers is a legitimate outcome, not a red flag: once the
        # sub-agents compile to agent_tool they are dispatched as SUB_WORKFLOWs built
        # at runtime inside the fork, so neither collectSimpleTaskNames() nor the
        # top-level worker-typed tool scan contributes anything. The leaf @tool
        # workers are still registered — the SDK derives those from its own
        # serialization, not from this list. What matters is only the direction
        # below: nothing may be *required* that cannot be *supplied*.
        required = set(compiled_plan.get("requiredWorkers") or [])

        _, workers = serialize_agent(_build_coordinator(model))
        available = {w.name for w in workers}

        print(f"  server requires : {sorted(required)}")
        print(f"  SDK can supply  : {sorted(available)}")

        unsatisfiable = required - available
        assert not unsatisfiable, (
            f"server requires {len(required)} workers but the SDK can only "
            f"supply {len(available)}; nothing can ever execute "
            f"{sorted(unsatisfiable)}. Tasks of these types stay SCHEDULED and "
            f"their JOIN stays IN_PROGRESS forever. "
            f"required={sorted(required)} available={sorted(available)}"
        )

    @pytest.mark.parametrize("run_index", range(RUNS))
    def test_single_turn_coordinator_completes(self, single_turn_runs, run_index):
        """The workflow must terminate. Pre-fix it hangs RUNNING forever.

        When the LLM calls the bare sub-agent name, the fork schedules a SIMPLE
        task typed with that name, no worker exists for it, and the JOIN waits
        on it indefinitely — no error, no timeout, no answer.
        """
        result = single_turn_runs[run_index]
        diag = _run_diagnostic(result)
        print(f"  {diag}")

        assert result.execution_id, f"[run {run_index + 1}] no execution_id. {diag}"
        assert result.status == "COMPLETED", (
            f"[run {run_index + 1}] expected COMPLETED, got '{result.status}' "
            f"after {TIMEOUT}s. A status of RUNNING here is the "
            f"FORK_JOIN_DYNAMIC deadlock — check whether the "
            f"forked SIMPLE task named after a sub-agent is still SCHEDULED. "
            f"{diag}"
        )

    @pytest.mark.parametrize("run_index", range(RUNS))
    def test_single_turn_coordinator_combines_both_specialists(
        self, single_turn_runs, run_index
    ):
        """Both specialists must contribute — that is what single_turn means.

        ``mode="single_turn"`` is call-and-return: the coordinator calls a
        sub-agent, gets its result, keeps looping, and composes the answer.
        The transfer path implements the opposite (permanent handoff), so it
        can only ever surface one specialist's output — which is why runs that
        *do* complete pre-fix still answer only half the question.
        """
        result = single_turn_runs[run_index]
        if result.status != "COMPLETED":
            pytest.skip(
                f"run {run_index + 1} did not complete "
                f"({result.status}) — see the completion test"
            )

        output = _output_text(result)
        print(f"  wf={result.execution_id} output={output[:300]}")

        missing = [
            label
            for label, sentinel in (
                ("weather", TEMP_SENTINEL),
                ("time", TIME_SENTINEL),
            )
            if sentinel not in output
        ]
        assert not missing, (
            f"[run {run_index + 1}] answer is missing the "
            f"{' and '.join(missing)} specialist's result. The coordinator was "
            f"asked to call both and combine them; a permanent transfer to one "
            f"sub-agent cannot do that. "
            f"{_run_diagnostic(result)} | output={output!r}"
        )
