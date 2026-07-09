# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Canonical metrics mode: opt-in harmonized metric surface via `WORKER_CANONICAL_METRICS=true` -- [details](METRICS.md#detailed-technical-notes--unreleased)
- `MetricsSettings` gains `clean_directory` and `clean_dead_pids` for opt-in stale `.db` file cleanup (both default to `False`)
- `SchedulerClient` now carries the schedule lifecycle operations itself: `pause(reason=)`, `resume`, `delete`, `run_now`, `preview_next`, `reconcile` (declarative tri-state sync) — with typed errors (`ScheduleNotFound`, `InvalidCronExpression`, ...). `pause_schedule` gains an optional `reason=` (stored by OSS Conductor servers; ignored by Orkes servers)

### Changed

- **Multiprocessing start method now defaults to `spawn` on all platforms** (was `fork` everywhere except Windows). `fork` caused silently-restarting `SIGSEGV` worker subprocesses on macOS (exitcode `-11`) and fork-with-held-lock deadlocks on POSIX. 
- Legacy metrics emit unchanged by default; no env var required
- `metrics_collector.py` is now a compatibility shim; `from conductor.client.telemetry.metrics_collector import MetricsCollector` continues to work
- **Breaking (scoped):** schedule client objects no longer expose the mapped `get`/`save`/`list_for_agent` wrappers — `SchedulerClient`'s native methods are the source of truth: `get(wire)` → `get_schedule(wire)`, `save(schedule, agent)` → `save_schedule(SaveScheduleRequest)`, `list_for_agent(agent)` → `get_all_schedules(workflow_name=agent)`. The module-level `schedules.list/get/save` functions (and their `ScheduleInfo` returns) are unchanged
- `get_schedule` returns a typed `WorkflowSchedule` (or `None` for missing schedules) instead of a raw camelCase dict, matching its declared annotation and [docs/SCHEDULE.md](docs/SCHEDULE.md); dict-consumers should switch to attribute access or `to_dict()`

### Deprecated

- `AgentScheduleClient`/`ScheduleClient` and `OrkesClients.get_agent_schedule_client()` — fully functional delegation shims over `SchedulerClient`; use `get_scheduler_client()`. Removal planned for the next major release

### Fixed

- `@worker_task` workers are now picklable, making the decorator path work with the `spawn`/`forkserver` start methods (fixes `TypeError: cannot pickle '_thread.lock' object` and `PicklingError: it's not the same object as ...`; issues #264, #271): `Worker.api_client` is created lazily in the worker process, runtime state (locks, pending async tasks, background loop) is excluded from pickling and rebuilt in the child, and decorated functions are pickled as importable references resolved in the child
- `TaskHandler.start_processes()` no longer hangs the interpreter when a worker fails to start (e.g., unpicklable state under `spawn`); it now cleans up already-started subprocesses and raises with actionable guidance
- Worker processes killed by a signal now log a diagnostic hint (signal number, `PYTHONFAULTHANDLER=1` guidance) instead of restarting silently
- Per-schedule pause/resume now work on both Conductor server families: the client sends `PUT` (the OSS Conductor dialect — the spec-generated `GET` failed there) and transparently falls back to `GET` on a 405 for Orkes servers, caching the working dialect per client instance
