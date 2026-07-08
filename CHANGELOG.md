# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Canonical metrics mode: opt-in harmonized metric surface via `WORKER_CANONICAL_METRICS=true` -- [details](METRICS.md#detailed-technical-notes--unreleased)
- `MetricsSettings` gains `clean_directory` and `clean_dead_pids` for opt-in stale `.db` file cleanup (both default to `False`)

### Changed

- **Multiprocessing start method now defaults to `spawn` on all platforms** (was `fork` everywhere except Windows). `fork` caused silently-restarting `SIGSEGV` worker subprocesses on macOS (exitcode `-11`) and fork-with-held-lock deadlocks on POSIX. 
- Legacy metrics emit unchanged by default; no env var required
- `metrics_collector.py` is now a compatibility shim; `from conductor.client.telemetry.metrics_collector import MetricsCollector` continues to work

### Fixed

- `@worker_task` workers are now picklable, making the decorator path work with the `spawn`/`forkserver` start methods (fixes `TypeError: cannot pickle '_thread.lock' object` and `PicklingError: it's not the same object as ...`; issues #264, #271): `Worker.api_client` is created lazily in the worker process, runtime state (locks, pending async tasks, background loop) is excluded from pickling and rebuilt in the child, and decorated functions are pickled as importable references resolved in the child
- `TaskHandler.start_processes()` no longer hangs the interpreter when a worker fails to start (e.g., unpicklable state under `spawn`); it now cleans up already-started subprocesses and raises with actionable guidance
- Worker processes killed by a signal now log a diagnostic hint (signal number, `PYTHONFAULTHANDLER=1` guidance) instead of restarting silently
