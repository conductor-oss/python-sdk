# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `conductor.ai.agents`: durable AI-agent authoring on top of the worker SDK. Author an `Agent` in code; `AgentRuntime` compiles it to a Conductor workflow and runs it — `run`/`start`/`deploy`/`serve`/`plan`/`stream` (each with an async twin), plus HITL/lifecycle verbs (`respond`/`approve`/`reject`/`send_message`/`signal`/`pause`/`cancel`/`stop`/`resume`) on the runtime and the returned `AgentHandle`. `AgentConfig` carries only runtime-behaviour knobs (worker pool, liveness); connection, auth, and log level come from the standard `Configuration`, resolved via `CONDUCTOR_SERVER_URL`/`CONDUCTOR_AUTH_*` (falling back to `AGENTSPAN_*` for source-SDK compatibility). `RunSettings` overrides an agent's `model`/`temperature`/`max_tokens`/`reasoning_effort`/`thinking_budget_tokens` for a single `run`/`start` call without rebuilding the agent.
- `OrkesClients.get_agent_client()` exposes the `/agent/*` control plane as a typed `AgentClient` (`start`/`deploy`/`compile`/`get_status`/`get_execution`/`list_executions`/`respond`/`stop`/`signal`/`stream_sse`/`close`, sync + async), built on the shared `ApiClient`/`AsyncApiClient` so JWT mint/cache/TTL-refresh/401-retry are inherited rather than reimplemented; SSE streaming borrows the same client's auth header via `ApiClient.get_authentication_headers()`.
- Tool-worker credentials are declared by name on a tool (`@tool(credentials=[...])`) and delivered wire-only via `TaskDef.runtimeMetadata` / `Task.runtimeMetadata` (requires a server implementing conductor-oss #1255) — injected into the worker's environment for that call only, never falling back to the ambient environment if a declared credential isn't delivered.
- A `ServerLivenessMonitor` detects a stalled or dead tool worker on stateful runs (`liveness_enabled`/`liveness_stall_seconds`/`liveness_check_interval_seconds` on `AgentConfig`) and fails `result()`/`join()` with a diagnosable stall error instead of blocking forever.
- Framework adapters (LangChain, LangGraph, OpenAI Agents SDK, Claude Agent SDK) run agents authored in those frameworks on the same durable runtime; every worker/tool callable the adapters register is spawn-safe (importable by qualified name, or a plain-config `PassthroughWorkerEntry`) under the default `spawn` start method.
- Canonical metrics mode: opt-in harmonized metric surface via `WORKER_CANONICAL_METRICS=true` -- [details](METRICS.md#detailed-technical-notes--unreleased)
- `MetricsSettings` gains `clean_directory` and `clean_dead_pids` for opt-in stale `.db` file cleanup (both default to `False`)
- `SchedulerClient` now carries the schedule lifecycle operations itself: `pause(reason=)`, `resume`, `delete`, `run_now`, `preview_next`, `reconcile` (declarative tri-state sync) — with typed errors (`ScheduleNotFound`, `InvalidCronExpression`, ...). `pause_schedule` gains an optional `reason=` (stored by OSS Conductor servers; ignored by Orkes servers)

### Changed

- **Multiprocessing start method now defaults to `spawn` on all platforms** (was `fork` everywhere except Windows). `fork` caused silently-restarting `SIGSEGV` worker subprocesses on macOS (exitcode `-11`) and fork-with-held-lock deadlocks on POSIX. 
- Legacy metrics emit unchanged by default; no env var required
- `metrics_collector.py` is now a compatibility shim; `from conductor.client.telemetry.metrics_collector import MetricsCollector` continues to work
- `get_schedule` returns a typed `WorkflowSchedule` (or `None` for missing schedules) instead of a raw camelCase dict, matching its declared annotation and [docs/SCHEDULE.md](docs/SCHEDULE.md); dict-consumers should switch to attribute access or `to_dict()`

### Fixed

- `@worker_task` workers are now picklable, making the decorator path work with the `spawn`/`forkserver` start methods (fixes `TypeError: cannot pickle '_thread.lock' object` and `PicklingError: it's not the same object as ...`; issues #264, #271): `Worker.api_client` is created lazily in the worker process, runtime state (locks, pending async tasks, background loop) is excluded from pickling and rebuilt in the child, and decorated functions are pickled as importable references resolved in the child
- `TaskHandler.start_processes()` no longer hangs the interpreter when a worker fails to start (e.g., unpicklable state under `spawn`); it now cleans up already-started subprocesses and raises with actionable guidance
- Worker processes killed by a signal now log a diagnostic hint (signal number, `PYTHONFAULTHANDLER=1` guidance) instead of restarting silently
- Per-schedule pause/resume now work on both Conductor server families: the client sends `PUT` (the OSS Conductor dialect — the spec-generated `GET` failed there) and transparently falls back to `GET` on a 405 for Orkes servers
