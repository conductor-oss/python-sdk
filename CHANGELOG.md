# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Metrics harmonization** - canonical metric surface aligned with the cross-SDK catalog, opt-in via `WORKER_CANONICAL_METRICS=true`
  - New `CanonicalMetricsCollector` emits the harmonized cross-SDK catalog using real Prometheus `Histogram`s for timing and size, replacing the legacy quantile-gauge timing shape. New canonical-only metrics: `task_poll_error_total`, `task_execution_started_total`, `task_result_size_bytes`, `workflow_input_size_bytes`, `http_api_client_request_seconds`, `active_workers`. Time buckets `0.001…10s`; size buckets `100…10_000_000` bytes.
  - `metrics_factory.create_metrics_collector(settings)` selects `LegacyMetricsCollector` (default) or `CanonicalMetricsCollector` based on `WORKER_CANONICAL_METRICS` (truthy: `true`, `1`, `yes`, case-insensitive, whitespace-trimmed). `WORKER_LEGACY_METRICS` is documented but not yet read.
  - New abstract `MetricsCollectorBase` consolidates Prometheus infrastructure (lazy `prometheus_client` imports, multiprocess `NoPidCollector` aggregation, HTTP server, exception-label cardinality bounding) and event handlers shared by both collectors.
  - `(Async)TaskRunner` now records `task_update_time` (`status="SUCCESS"` / `"FAILURE"`) on every update path.
  - `OrkesWorkflowClient.start_workflow*` records workflow input payload size and increments `workflow_start_error` on exception; `OrkesClients` / `OrkesBaseClient` accept an optional `metrics_collector`.
  - `create_metrics_collector` partitions the metrics directory into a `legacy/` or `canonical/` subdirectory, so switching implementations never produces stale metric names from the previous type.
  - `MetricsSettings` gains `clean_directory` (default `False`) to wipe all `.db` files and `clean_dead_pids` (default `False`) to remove only `.db` files from PIDs that no longer exist. Both are executed by the factory against the final partitioned subdirectory.
  - `CONDUCTOR_MP_START_METHOD` env var (`spawn` / `fork` / `forkserver`; default `fork` on POSIX, `spawn` on Windows) to control the worker pool's multiprocessing start method (motivated by a `prometheus_client` lock-fork deadlock).
  - Harness manifest sets `WORKER_CANONICAL_METRICS=true`; `harness/main.py` logs which collector is active.

### Changed

- **Metrics harmonization** - defaults preserved; legacy metrics emit unchanged when `WORKER_CANONICAL_METRICS` is unset
  - `MetricLabel.PAYLOAD_TYPE` retains its original value `"payload_type"`; a new `PAYLOAD_TYPE_CAMEL = "payloadType"` constant is used only by the canonical collector on `external_payload_used_total`.
  - `metrics_collector.py` is now a thin compatibility shim: `MetricsCollector = LegacyMetricsCollector`, so `from conductor.client.telemetry.metrics_collector import MetricsCollector` continues to work.
  - Default behavior is unchanged: with no env var set, the legacy metric names, label conventions, and quantile-gauge timing shape from prior releases are preserved.
  - Rewrote `METRICS.md` to document both surfaces, the env-var gate, full canonical and legacy catalogs, labels, a "Migrating From Legacy to Canonical" mapping (including the `payload_type` → `payloadType` label change and PromQL replacements), and troubleshooting.
  - Updated `README.md`, `WORKER_CONFIGURATION.md`, and `docs/design/WORKER_DESIGN.md` to point at `METRICS.md`.
