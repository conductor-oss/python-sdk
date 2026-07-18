# Examples Verification Report

**Date:** 2026-07-18 · **Base:** `7481aed2`

Full verification of the SDK example catalog against a live Conductor server. This
report tracks the status of each suite so it can be re-checked as the SDK and server
evolve. **This PR is report + documentation only** — fixes for the bugs found are
proposed separately as a draft PR, pending a decision on whether to take them.

## Environment

| Component | Value |
|-----------|-------|
| Server | conductor-oss **3.32.0-rc.8** boot JAR (Maven Central), `java -jar --server.port=8080` |
| Python | 3.12.13 (uv venv), `pip install -e '.[agents]'` |
| Platform | macOS (darwin arm64) — worker processes use the **spawn** start method |
| LLM | `AGENTSPAN_LLM_MODEL=openai/gpt-4o-mini`, `OPENAI_API_KEY` + `ANTHROPIC_API_KEY` set |
| Harness | `examples/agents/run_all_examples.py --jobs 8 --timeout 360` + curated core-example runner |

### ⚠️ Server version requirement (root cause of the most common failure)

The agent examples need the **agent runtime**, on by default from conductor-oss
**3.32.0-rc.8** (the version pinned in `.github/workflows/agent-e2e.yml`). The `latest`
JAR installed by `conductor server start` is the 3.30.x stable line, which has **no
`/api/agent/*` endpoints** — every agent example fails with
`AgentNotFoundError: HTTP 404 ... api/agent/start`. On 3.30.2 the suite scored
3 PASS / 103 ERROR; on 3.32.0-rc.8 (same code) it scored 96 PASS / 2 ERROR.

Workaround (works today, `conductor-server-3.32.0-rc.8.jar` is already in the CLI's S3
bucket): `conductor server start --version 3.32.0-rc.8`. Decision: do **not** repoint
the CLI's floating `latest` at an rc — this resolves itself when 3.32.0 GA ships.

## Results — agents suite (`examples/agents/`, 146 files)

`run_all_examples.py` with the fixes from the companion fixes PR applied:

| Status | Count | Notes |
|--------|------:|-------|
| PASS | 96 | end-to-end against the live server, real LLM calls |
| SKIP | 46 | interactive / daemon-by-design / external infra (MCP, Docker, Kafka, Slack, OCG, skills repo, messages API) |
| ERROR | 2 | see "Remaining failures" |
| HUNG | 2 | see "Remaining failures" |

Before fixes (same server): 91 PASS / 12 ERROR / 3 HUNG / 40 SKIP.

## Results — core suite (curated, 18 examples)

| Example | Status | Notes |
|---------|--------|-------|
| workers_e2e.py | ✅ fixed | workers run clean; e2e workflow COMPLETED server-side; blocks on `join_processes()` by design |
| worker_example.py | ✅ fixed | runs clean as a worker daemon |
| task_listener_example.py | ✅ fixed | all workers start, listeners fire, no spawn errors |
| helloworld/helloworld.py | ✅ fixed | exits 0 |
| worker_configuration_example.py | ✅ | |
| task_workers.py | ✅ | |
| dynamic_workflow.py | ✅ | |
| workflow_ops.py | ✅ | |
| workflow_status_listner.py | ✅ | |
| kitchensink.py | ✅ | |
| task_configure.py | ✅ | |
| metadata_journey_oss.py | ✅ | |
| schedule_journey.py | ✅ | |
| event_listener_examples.py | ✅ | |
| lease_extension_example.py | ✅ | ~62s |
| agentic_workflows/llm_chat.py | ✅ fixed | previously a **false pass** — reported success while the workflow FAILED server-side |
| task_context_example.py | ➖ daemon | runs until Ctrl+C by design; workers run clean |
| agentic_workflows/function_calling_example.py | ➖ interactive | reads stdin; not runnable headless |

Static check: every `.py` under `examples/` compiles (`compileall`). Unit tests:
`tests/unit/ai` — 1744 passed.

## Bugs found (fixes proposed in the companion draft PR)

Statuses marked "fixed" below and in the tables above reflect runs **with the
companion PR's fixes applied**; without them, each item reproduces as described.

1. **`examples/helloworld/greetings_worker.py` — duplicate `def greet`.** The module
   defined `greet` twice (tasks `greet` and `greet_sync`); the second shadowed the
   first, so spawn-pickling the first failed with
   `PicklingError: not the same object as helloworld.greetings_worker.greet`. Broke
   `workers_e2e.py`, `helloworld.py`, and `task_listener_example.py` on macOS/Windows.
   Renamed the second function `greet_sync`.

2. **`src/conductor/ai/agents/tool.py` — SDK bug: worker-task tool lookup broken after
   re-registration.** `ToolRegistry.register_tool_workers` overwrites a
   `@worker_task` tool's `_decorated_functions` entry with a spawn-safe
   `ToolWorkerEntry` wrapper; the identity check in `_try_worker_task` then failed for
   the same tool later in the same run
   (`TypeError: Expected a @tool-decorated function ...`). Broke
   `14_existing_workers.py`. The lookup now walks `__wrapped__` chains and the
   wrapper's `fn_direct`/`fn_ref` carriers. Two regression tests added.

3. **`examples/worker_example.py` — hardcoded `/Users/viren/` metrics path.**
   `PermissionError` on any other machine. Now uses `tempfile.gettempdir()`.

4. **`examples/user_example/user_workers.py` — inconsistent package identity.**
   Imported `examples.user_example.models` while every consumer loads the module as
   `user_example.user_workers`; spawn children (which only inherit `PYTHONPATH`, not
   runtime `sys.path` edits) crashed. Import is now package-relative-consistent.

5. **`examples/agents/kitchen_sink.py` — `@agent` classifiers declared a required
   `prompt` arg.** `@agent`-decorated functions are invoked with zero args at compile
   time for dynamic instructions → `TypeError`. Signatures fixed.

6. **`examples/agents/16i/16j` — tools defined inside factory functions.**
   `<locals>` callables can't be re-imported by spawn workers →
   `SpawnSafetyError`. Tools hoisted to module level; both now pass.

7. **`examples/agents/94_openai_runner_tools.py` — `@function_tool` rebinding.** The
   decorator rebinds the module global to a `FunctionTool`, so the extracted original
   couldn't be pickled by reference. The example now keeps the plain function at module
   level and applies `function_tool()` at `Agent(...)` construction; passes end-to-end.

8. **`examples/agentic_workflows/llm_chat.py` — two bugs.** (a) Two LLM tasks sent
   **system-only** message lists; the server requires a non-empty user message and
   failed the workflow before the first task ran. (b) The example treated any terminal
   state as success (`is_completed()`), printing "Conversation complete." over a FAILED
   workflow and exiting 0. Both fixed; a full 3-turn conversation now completes.

9. **`examples/agents/run_all_examples.py` — skip-list updates.** Six examples that
   need infra this environment (and CI's pinned server) don't provide are now
   classified SKIP with reasons: `30`/`32` (need the `dg` skill cloned into
   `~/.claude/skills/dg`), `75`/`82`/`83`/`84` (need the workflow *messages* API,
   `GET /api/workflow/{id}/messages`, which is not in conductor-oss 3.32.0-rc.8).

10. **`examples/agents/README.md`** — added the server-version requirement + start
    commands; fixed the provider/model table (OpenAI row showed the Anthropic default
    string); renumbered setup steps. **`examples/README.md`** — added the same server
    note to the AI Agents section.

## Remaining failures (known, not fixed here)

| Example | Status | Diagnosis |
|---------|--------|-----------|
| `agents/kitchen_sink.py` | ERROR | Fixed classifier TypeError, now fails server-side: `HTTP 500 — The Task translation_swarm defined as a sub-workflow has no workflow definition available`. Sub-workflow (SWARM strategy) definitions aren't registered before `/agent/start` on conductor-oss rc.8. Needs SDK/server investigation. |
| `agents/74_cli_error_output.py` | FLAKY | LLM-behavior assertion: the agent paraphrases stderr instead of quoting it verbatim; passes/fails depending on model output. Consider loosening the assertion or pinning a stricter prompt. |
| `agents/86_coding_agent.py` | HUNG | Does not finish within 420s even running solo. Needs investigation (or reclassification if it is expected to be long-running). |
| `agents/68_context_condensation.py` | SLOW | Passes solo in ~346s; exceeds the suite timeout under 8-way contention. Consider `--timeout 480` for suite runs or trimming the example. |

## SDK observations (follow-ups, out of scope for this PR)

- **`AgentNotFoundError` should name the server-version requirement.** When
  `/api/agent/start` 404s ("No static resource"), the error in
  `orkes_agent_client.py` should suggest conductor-oss ≥ 3.32.0-rc.8 and the
  `conductor server start --version` command. This would have made the most common
  failure self-explanatory.
- **`run_all_examples.py` preflight**: check `GET /api/version` + probe an agent
  endpoint before launching 100+ subprocesses against a server that can't run them.
- **openai-agents `@function_tool` at module level is spawn-unsafe by construction**
  (the global is rebound to a `FunctionTool`; the original function is only reachable
  through a closure, which `FunctionRef` can't express). Teaching the spawn-safety
  layer a closure hop — or documenting the `function_tool(fn)`-at-construction pattern
  — would let users keep the upstream OpenAI sample shape.

## How to reproduce

```bash
# server
curl -fL -o conductor-server.jar "https://repo1.maven.org/maven2/org/conductoross/conductor-server/3.32.0-rc.8/conductor-server-3.32.0-rc.8-boot.jar"
OPENAI_API_KEY=... ANTHROPIC_API_KEY=... java -jar conductor-server.jar --server.port=8080

# SDK + suite
uv venv --python 3.12 .venv && VIRTUAL_ENV=$PWD/.venv uv pip install -e '.[agents]'
export CONDUCTOR_SERVER_URL=http://localhost:8080/api AGENTSPAN_LLM_MODEL=openai/gpt-4o-mini
python examples/agents/run_all_examples.py --jobs 8 --timeout 360
```
