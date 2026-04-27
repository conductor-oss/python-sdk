# Metrics Documentation

The Conductor Python SDK includes built-in metrics collection using Prometheus to monitor worker performance, API requests, and task execution.

## Table of Contents

- [Quick Reference](#quick-reference)
- [Configuration](#configuration)
- [Metric Types](#metric-types)
- [Examples](#examples)
- [Breaking change: timing metrics moved to real Histograms](#breaking-change-timing-metrics-moved-to-real-histograms)
- [Deprecations](#deprecations)

## Quick Reference

### Canonical metrics (emitted today)

| Metric | Type | Labels | Meaning |
|---|---|---|---|
| `task_poll_total` | Counter | `taskType` | Incremented for every poll request issued to the server. |
| `task_poll_error_total` | Counter | `taskType`, `exception` | Client-side poll failures (HTTP / deserialization / timeout). `exception` is the exception class name. |
| `task_execution_started_total` | Counter | `taskType` | Incremented when a polled task is dispatched to the user worker function. |
| `task_execute_error_total` | Counter | `taskType`, `exception` | User worker raised an exception. |
| `task_update_error_total` | Counter | `taskType`, `exception` | Task-result update back to the server failed. |
| `task_ack_error_total` | Counter | `taskType`, `exception` | Exception while acknowledging a polled task. |
| `task_ack_failed_total` | Counter | `taskType` | Server responded with a non-success ack (no exception raised). |
| `task_execution_queue_full_total` | Counter | `taskType` | Worker's internal executor queue saturated; poll rejected a task. |
| `task_paused_total` | Counter | `taskType` | Poll happened while the worker was paused. |
| `thread_uncaught_exceptions_total` | Counter | — | Uncaught exception inside a worker thread. |
| `worker_restart_total` | Counter | `taskType` | TaskHandler restarted a worker subprocess (Python-only). |
| `external_payload_used_total` | Counter | `entityName`, `operation`, `payload_type` | External payload storage used (READ / WRITE). |
| `workflow_start_error_total` | Counter | `workflowType`, `exception` | `startWorkflow` failed client-side. |
| `task_poll_time_seconds` | **Histogram** | `taskType`, `status` | Task poll latency (seconds). Emits `_bucket{le=...}`, `_count`, `_sum`. |
| `task_execute_time_seconds` | **Histogram** | `taskType`, `status` | Task execution latency. |
| `task_update_time_seconds` | **Histogram** | `taskType`, `status` | Task-update (result-report) latency. |
| `http_api_client_request_seconds` | **Histogram** | `method`, `uri`, `status` | HTTP API client request latency. |
| `task_result_size_bytes` | Gauge | `taskType` | Last-seen task-result payload size. |
| `workflow_input_size_bytes` | Gauge | `workflowType`, `version` | Last-seen workflow-input payload size. |

The bucket set used by all four Histograms is `(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)` seconds — matched to the canonical set in [`sdk-metrics-harmonization.md`](https://github.com/orkes-io/certification-cloud-util/blob/main/sdk-metrics-harmonization.md).

### Deprecated metrics (still emitted for backward compatibility)

| Metric | Replacement |
|---|---|
| `task_poll_time` (Gauge) | `task_poll_time_seconds` (Histogram) |
| `task_execute_time` (Gauge) | `task_execute_time_seconds` (Histogram) |
| `task_result_size` (Gauge) | `task_result_size_bytes` (Gauge, same value) |
| `workflow_input_size` (Gauge) | `workflow_input_size_bytes` (Gauge, same value) |

### Label values

- `status` (task time histograms): `SUCCESS`, `FAILURE`
- `status` (`http_api_client_request_seconds`): HTTP status code as a string, or `"0"` / `"error"` on transport failure
- `method`: `GET`, `POST`, `PUT`, `DELETE`, etc.
- `uri`: API endpoint **path template**, not the interpolated path (e.g. `/tasks/poll/batch/{taskType}`)
- `exception`: exception class name (bounded cardinality), e.g. `<class 'conductor.client.http.rest.ApiException'>`
- `operation` / `payload_type`: `READ` / `WRITE`, `TASK_INPUT` / `TASK_OUTPUT` / `WORKFLOW_INPUT` / `WORKFLOW_OUTPUT`

### Example Prometheus output

```prometheus
# HTTP API client request latency (Histogram — real _bucket/_count/_sum)
http_api_client_request_seconds_bucket{method="GET",uri="/tasks/poll/batch/myTask",status="200",le="0.1"} 987.0
http_api_client_request_seconds_bucket{method="GET",uri="/tasks/poll/batch/myTask",status="200",le="+Inf"} 1000.0
http_api_client_request_seconds_count{method="GET",uri="/tasks/poll/batch/myTask",status="200"} 1000.0
http_api_client_request_seconds_sum{method="GET",uri="/tasks/poll/batch/myTask",status="200"} 114.5

# Task poll
task_poll_total{taskType="myTask"} 10264.0
task_poll_time_seconds_bucket{taskType="myTask",status="SUCCESS",le="0.05"} 940.0
task_poll_time_seconds_count{taskType="myTask",status="SUCCESS"} 1000.0
task_poll_error_total{taskType="myTask",exception="<class 'conductor.client.http.rest.ApiException'>"} 3.0

# Task execution
task_execution_started_total{taskType="myTask"} 120.0
task_execute_time_seconds_bucket{taskType="myTask",status="SUCCESS",le="0.01"} 119.0
task_execute_error_total{taskType="myTask",exception="<class 'TimeoutError'>"} 3.0

# Task update
task_update_time_seconds_bucket{taskType="myTask",status="SUCCESS",le="0.1"} 15.0
task_update_time_seconds_count{taskType="myTask",status="SUCCESS"} 15.0
```

## Configuration

### Enabling Metrics

Metrics are enabled by providing a `MetricsSettings` object when creating a `TaskHandler`:

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.automator.task_handler import TaskHandler

metrics_settings = MetricsSettings(
    directory='/path/to/metrics',
    file_name='conductor_metrics.prom',
    update_interval=10
)

api_config = Configuration(
    server_api_url='http://localhost:8080/api',
    debug=False
)

with TaskHandler(
    configuration=api_config,
    metrics_settings=metrics_settings,
    workers=[...]
) as task_handler:
    task_handler.start_processes()
```

### AsyncIO Workers

Usage with TaskHandler:

```python
from conductor.client.automator.task_handler import TaskHandler

with TaskHandler(
    configuration=api_config,
    metrics_settings=metrics_settings,
    scan_for_annotated_workers=True,
    import_modules=['your_module']
) as task_handler:
    task_handler.start_processes()
    task_handler.join_processes()
```

### Metrics File Cleanup

For multiprocess workers using Prometheus multiprocess mode, clean the metrics directory on startup to avoid stale data:

```python
import os
import shutil

metrics_dir = '/path/to/metrics'
if os.path.exists(metrics_dir):
    shutil.rmtree(metrics_dir)
os.makedirs(metrics_dir, exist_ok=True)

metrics_settings = MetricsSettings(
    directory=metrics_dir,
    file_name='conductor_metrics.prom',
    update_interval=10
)
```

## Metric Types

### Histograms (timing metrics)

Timing metrics are Prometheus **Histograms**. Each observation increments `_bucket{le="…"}` counts, `_count`, and `_sum`. Percentiles are computed server-side with `histogram_quantile()`, which means they aggregate correctly across multiple worker replicas / processes.

```promql
# p95 task execution latency for a given task type
histogram_quantile(
  0.95,
  sum by (le) (rate(task_execute_time_seconds_bucket{taskType="myTask",status="SUCCESS"}[5m]))
)
```

### Counters

Counters monotonically increase within a process lifetime. The `_total` suffix is added by `prometheus_client` automatically. Use `rate()` for per-second arrival, `increase()` for totals over a range.

### Size Gauges

`task_result_size_bytes` and `workflow_input_size_bytes` are last-value Gauges. Aggregation across replicas is not meaningful; use them for spot-checks and as dashboard overlays.

## Examples

### Querying Metrics with PromQL

**Average API request latency:**

```promql
rate(http_api_client_request_seconds_sum[5m])
/
rate(http_api_client_request_seconds_count[5m])
```

**API error rate:**

```promql
sum(rate(http_api_client_request_seconds_count{status=~"4..|5.."}[5m]))
/
sum(rate(http_api_client_request_seconds_count[5m]))
```

**Task poll success rate:**

```promql
sum(rate(task_poll_time_seconds_count{status="SUCCESS"}[5m]))
/
sum(rate(task_poll_time_seconds_count[5m]))
```

**p95 task execution latency:**

```promql
histogram_quantile(
  0.95,
  sum by (le, taskType) (rate(task_execute_time_seconds_bucket[5m]))
)
```

**Slowest API endpoints (p99):**

```promql
topk(
  10,
  histogram_quantile(
    0.99,
    sum by (le, uri) (rate(http_api_client_request_seconds_bucket[5m]))
  )
)
```

### Complete Example

```python
import os
import shutil
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.worker.worker_interface import WorkerInterface

metrics_dir = os.path.join(os.path.expanduser('~'), 'conductor_metrics')
if os.path.exists(metrics_dir):
    shutil.rmtree(metrics_dir)
os.makedirs(metrics_dir, exist_ok=True)

metrics_settings = MetricsSettings(
    directory=metrics_dir,
    file_name='conductor_metrics.prom',
    update_interval=10
)

api_config = Configuration(
    server_api_url='http://localhost:8080/api',
    debug=False
)

class MyWorker(WorkerInterface):
    def execute(self, task):
        return {'status': 'completed'}

    def get_task_definition_name(self):
        return 'my_task'

with TaskHandler(
    configuration=api_config,
    metrics_settings=metrics_settings,
    workers=[MyWorker()]
) as task_handler:
    task_handler.start_processes()
```

### Scraping with Prometheus

Configure Prometheus to scrape the metrics HTTP server (recommended — set `http_port` on `MetricsSettings`) or consume the file produced by the multiprocess writer:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'conductor-python-sdk'
    static_configs:
      - targets: ['localhost:8000']
```

## Breaking change: timing metrics moved to real Histograms

Starting with this release, the following four metrics switched from a custom sliding-window Gauge implementation (which emitted `{quantile="…"}` samples plus synthetic `_count`/`_sum` Gauges) to real `prometheus_client.Histogram` instances:

- `task_poll_time_seconds`
- `task_execute_time_seconds`
- `task_update_time_seconds` (previously never fired — now wired into the task update path)
- `http_api_client_request_seconds` (previously named `http_api_client_request`)

**Output shape change:** samples like

```
task_poll_time_seconds{taskType="myTask",status="SUCCESS",quantile="0.95"} 0.12
```

no longer exist. Instead you get the standard Histogram shape:

```
task_poll_time_seconds_bucket{taskType="myTask",status="SUCCESS",le="0.1"} N
task_poll_time_seconds_bucket{taskType="myTask",status="SUCCESS",le="+Inf"} M
task_poll_time_seconds_count{taskType="myTask",status="SUCCESS"} M
task_poll_time_seconds_sum{taskType="myTask",status="SUCCESS"} S
```

Dashboards that selected on the `quantile` label must switch to `histogram_quantile()`:

```promql
# Before:
task_poll_time_seconds{quantile="0.95"}

# After:
histogram_quantile(
  0.95,
  sum by (le, taskType) (rate(task_poll_time_seconds_bucket[5m]))
)
```

This change is intentional. The previous sliding-window implementation could not aggregate percentiles correctly across worker processes or replicas — `histogram_quantile` over real `_bucket` samples can.

## Deprecations

The following metrics are still emitted for backward compatibility but will be removed in a future major release. Prefer their canonical replacements (see [Quick Reference](#quick-reference)).

| Deprecated | Replacement | Notes |
|---|---|---|
| `task_poll_time` (Gauge) | `task_poll_time_seconds` (Histogram) | Gauge keeps showing only the most recent sample; Histogram is aggregatable. |
| `task_execute_time` (Gauge) | `task_execute_time_seconds` (Histogram) | Same. |
| `task_result_size` (Gauge) | `task_result_size_bytes` (Gauge) | Same value, canonical name. |
| `workflow_input_size` (Gauge) | `workflow_input_size_bytes` (Gauge) | Same value, canonical name. |

## Troubleshooting

### Metrics file is empty

- Ensure `MetricsCollector` is registered as an event listener or that `metrics_settings` is passed to `TaskHandler`.
- Check that workers are actually polling and executing tasks.
- Verify the metrics directory has write permissions.

### Stale metrics after restart

- Clean the metrics directory on startup (see Configuration section).
- Prometheus `multiprocess` mode requires cleanup between runs.

### Missing metrics

- Verify `metrics_settings` is passed to `TaskHandler`.
- Check that the SDK version supports the metric you're looking for.
- Ensure workers are properly registered and running.
