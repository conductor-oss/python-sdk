# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Canonical metrics mode: opt-in harmonized metric surface via `WORKER_CANONICAL_METRICS=true` -- [details](METRICS.md#detailed-technical-notes--unreleased)
- `MetricsSettings` gains `clean_directory` and `clean_dead_pids` for opt-in stale `.db` file cleanup (both default to `False`)
- `CONDUCTOR_MP_START_METHOD` env var to control the worker pool's multiprocessing start method

### Changed

- Legacy metrics emit unchanged by default; no env var required
- `metrics_collector.py` is now a compatibility shim; `from conductor.client.telemetry.metrics_collector import MetricsCollector` continues to work
