# Python SDK Metrics

The Conductor Python SDK can expose Prometheus metrics for worker polling, task
execution, task updates, workflow starts, external payload usage, and generated
API-client HTTP calls.

The SDK currently has two mutually exclusive metric surfaces:

- **Legacy metrics** are the default. They preserve the pre-harmonization Python
  SDK names and shapes, including sliding-window quantile gauges for timing
  metrics.
- **Canonical metrics** are opt-in with `WORKER_CANONICAL_METRICS=true`. They
  use the cross-SDK canonical names, labels, units, and Prometheus histogram
  shapes.

Only one collector is active in a worker process. The SDK does not emit legacy
and canonical metrics at the same time.

Metric names below are the names exposed in Prometheus text output. The Python
`prometheus_client` library appends `_total` to counters in exposition output.

## Configuration

Enable metrics by passing `MetricsSettings` to `TaskHandler`.

```python
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings

config = Configuration()
metrics = MetricsSettings(
    directory="/tmp/conductor-metrics",
    http_port=8000,
)

with TaskHandler(
    configuration=config,
    metrics_settings=metrics,
    scan_for_annotated_workers=True,
) as task_handler:
    task_handler.start_processes()
    task_handler.join_processes()
```

With `http_port` set, the SDK starts a Prometheus-compatible HTTP endpoint:

```shell
curl http://localhost:8000/metrics
curl http://localhost:8000/health
```

Without `http_port`, the SDK writes Prometheus text output to
`{directory}/{file_name}` at `update_interval` seconds:

```python
metrics = MetricsSettings(
    directory="/tmp/conductor-metrics",
    file_name="conductor_metrics.prom",
    update_interval=10,
    http_port=None,
)
```

`MetricsSettings` cleans stale Prometheus multiprocess `.db` files by default.
Use a dedicated metrics directory per worker process group.

## Selecting Canonical Metrics

Set `WORKER_CANONICAL_METRICS` before the worker starts:

```shell
WORKER_CANONICAL_METRICS=true python my_worker.py
```

Accepted true values are `true`, `1`, and `yes`, case-insensitive. Any other
value, or an unset variable, selects legacy metrics. The variable is read when
the metrics collector is created, so changing it requires a worker restart.

## Canonical Metrics

Canonical timing values are seconds. Canonical size values are bytes. Label
names use camelCase.

Metrics are created lazily. A metric appears in `/metrics` only after the
corresponding worker event or collector method records it. Some low-level
surface metrics, such as ack, queue-full, paused, and uncaught-exception
counters, may not appear in normal worker runs unless that path is exercised.

### Canonical Counters

| Metric | Labels | Description |
|---|---|---|
| `task_poll_total` | `taskType` | Incremented each time the worker issues a poll request. |
| `task_execution_started_total` | `taskType` | Incremented when a polled task is dispatched to the worker function. |
| `task_poll_error_total` | `taskType`, `exception` | Incremented when a poll request fails client-side. |
| `task_execute_error_total` | `taskType`, `exception` | Incremented when the worker function throws. |
| `task_update_error_total` | `taskType`, `exception` | Incremented when updating the task result fails. |
| `task_ack_error_total` | `taskType`, `exception` | Collector surface for task ack errors. |
| `task_ack_failed_total` | `taskType` | Collector surface for failed task ack responses. |
| `task_execution_queue_full_total` | `taskType` | Collector surface for execution queue saturation events. |
| `task_paused_total` | `taskType` | Collector surface for polls skipped while the worker is paused. |
| `thread_uncaught_exceptions_total` | `exception` | Collector surface for uncaught worker-thread exceptions. |
| `worker_restart_total` | `taskType` | Python-only counter for TaskHandler subprocess restarts. |
| `external_payload_used_total` | `entityName`, `operation`, `payloadType` | Incremented when external payload storage is used. |
| `workflow_start_error_total` | `workflowType`, `exception` | Incremented when starting a workflow fails client-side. |

### Canonical Time Histograms

All canonical time histograms use buckets:
`0.001`, `0.005`, `0.01`, `0.025`, `0.05`, `0.1`, `0.25`, `0.5`, `1`, `2.5`,
`5`, `10`.

| Metric | Labels | Description |
|---|---|---|
| `task_poll_time_seconds` | `taskType`, `status` | Poll request latency. `status` is `SUCCESS` or `FAILURE`. |
| `task_execute_time_seconds` | `taskType`, `status` | Worker function execution duration. `status` is `SUCCESS` or `FAILURE`. |
| `task_update_time_seconds` | `taskType`, `status` | Task-result update latency. `status` is `SUCCESS` or `FAILURE`. |
| `http_api_client_request_seconds` | `method`, `uri`, `status` | Generated API-client HTTP request latency. |

Each histogram exposes Prometheus series such as:

```prometheus
task_execute_time_seconds_bucket{taskType="my_task",status="SUCCESS",le="0.1"} 42.0
task_execute_time_seconds_count{taskType="my_task",status="SUCCESS"} 50.0
task_execute_time_seconds_sum{taskType="my_task",status="SUCCESS"} 2.3
```

### Canonical Size Histograms

All canonical size histograms use buckets:
`100`, `1000`, `10000`, `100000`, `1000000`, `10000000`.

| Metric | Labels | Description |
|---|---|---|
| `task_result_size_bytes` | `taskType` | Serialized task result output size. |
| `workflow_input_size_bytes` | `workflowType`, `version` | Serialized workflow input size. |

### Canonical Gauges

| Metric | Labels | Description |
|---|---|---|
| `active_workers` | `taskType` | Current number of workers actively executing a task. |

## Legacy Metrics

Legacy mode is the default so existing dashboards and alerts continue to work.
Timing metrics are sliding-window quantile gauges over the latest 1,000
observations. Legacy timing metrics also expose `_count` and `_sum` gauge
series for the current sliding window.

As in canonical mode, metrics are created lazily and rare or surface-only
counters appear only when the corresponding code path records them.

### Legacy Counters

| Metric | Labels | Description |
|---|---|---|
| `task_poll_total` | `taskType` | Incremented each time polling is done. |
| `task_execute_error_total` | `taskType`, `exception` | Task execution errors. `exception` is `str(exception)`. |
| `task_update_error_total` | `taskType`, `exception` | Task update errors. `exception` is `str(exception)`. |
| `task_ack_error_total` | `taskType`, `exception` | Collector surface for task ack errors. `exception` is `str(exception)`. |
| `task_ack_failed_total` | `taskType` | Collector surface for failed task ack responses. |
| `task_execution_queue_full_total` | `taskType` | Collector surface for execution queue saturation events. |
| `task_paused_total` | `taskType` | Collector surface for polls skipped while the worker is paused. |
| `thread_uncaught_exceptions_total` | none | Collector surface for uncaught worker-thread exceptions. |
| `worker_restart_total` | `taskType` | TaskHandler subprocess restarts. |
| `external_payload_used_total` | `entityName`, `operation`, `payload_type` | External payload storage usage. |
| `workflow_start_error_total` | `workflowType`, `exception` | Workflow start errors. `exception` is `str(exception)`. |

Legacy mode does not emit `task_poll_error_total`,
`task_execution_started_total`, or `active_workers`.

### Legacy Time Metrics

| Metric | Type | Labels | Description |
|---|---|---|---|
| `task_poll_time` | Gauge | `taskType` | Most recent poll duration, in seconds. |
| `task_poll_time_seconds` | Quantile gauge | `taskType`, `status`, `quantile` | Sliding-window poll latency quantiles. |
| `task_poll_time_seconds_count` | Gauge | `taskType`, `status` | Sliding-window poll observation count. |
| `task_poll_time_seconds_sum` | Gauge | `taskType`, `status` | Sliding-window poll duration sum. |
| `task_execute_time` | Gauge | `taskType` | Most recent task execution duration, in seconds. |
| `task_execute_time_seconds` | Quantile gauge | `taskType`, `status`, `quantile` | Sliding-window execution latency quantiles. |
| `task_execute_time_seconds_count` | Gauge | `taskType`, `status` | Sliding-window execution observation count. |
| `task_execute_time_seconds_sum` | Gauge | `taskType`, `status` | Sliding-window execution duration sum. |
| `task_update_time_seconds` | Quantile gauge | `taskType`, `status`, `quantile` | Sliding-window task update latency quantiles. |
| `task_update_time_seconds_count` | Gauge | `taskType`, `status` | Sliding-window task update observation count. |
| `task_update_time_seconds_sum` | Gauge | `taskType`, `status` | Sliding-window task update duration sum. |
| `http_api_client_request` | Quantile gauge | `method`, `uri`, `status`, `quantile` | Sliding-window API-client request latency quantiles. |
| `http_api_client_request_count` | Gauge | `method`, `uri`, `status` | Sliding-window API-client request observation count. |
| `http_api_client_request_sum` | Gauge | `method`, `uri`, `status` | Sliding-window API-client request duration sum. |

### Legacy Size Gauges

| Metric | Labels | Description |
|---|---|---|
| `task_result_size` | `taskType` | Most recent serialized task result output size, in bytes. |
| `workflow_input_size` | `workflowType`, `version` | Most recent serialized workflow input size, in bytes. |

## Labels

| Label | Used by | Values |
|---|---|---|
| `taskType` | Worker metrics | Task definition name. |
| `workflowType` | Workflow metrics | Workflow definition name. |
| `version` | `workflow_input_size`, `workflow_input_size_bytes` | Workflow version as a string. If absent, the SDK uses `1`. |
| `status` | Task time metrics | `SUCCESS` or `FAILURE`. For HTTP metrics, the response code as a string, an exception `status` or `code`, or `error` when unavailable. |
| `exception` | Error counters | Legacy uses `str(exception)`. Canonical uses the exception class name, such as `TimeoutError`. |
| `entityName` | `external_payload_used_total` | Task type or workflow name associated with the external payload. |
| `operation` | `external_payload_used_total` | External payload operation, such as `READ` or `WRITE`. |
| `payload_type` | Legacy `external_payload_used_total` | Payload type, such as `TASK_INPUT`, `TASK_OUTPUT`, `WORKFLOW_INPUT`, or `WORKFLOW_OUTPUT`. |
| `payloadType` | Canonical `external_payload_used_total` | Payload type, such as `TASK_INPUT`, `TASK_OUTPUT`, `WORKFLOW_INPUT`, or `WORKFLOW_OUTPUT`. |
| `method` | HTTP metrics | HTTP verb. |
| `uri` | HTTP metrics | Request path passed by the generated API client. |
| `quantile` | Legacy time metrics | `0.5`, `0.75`, `0.9`, `0.95`, or `0.99`. |

## Migrating From Legacy to Canonical

Canonical mode is opt-in during the deprecation period. Before switching a
production worker, update dashboards and alerts against a staging worker with
`WORKER_CANONICAL_METRICS=true`.

Key changes:

- Time and size distribution metrics are real Prometheus histograms in
  canonical mode. Query `_bucket` series with `histogram_quantile()` instead of
  reading `{quantile="..."}` gauges.
- Legacy last-value gauges `task_poll_time`, `task_execute_time`,
  `task_result_size`, and `workflow_input_size` are not emitted in canonical
  mode.
- Canonical adds `task_poll_error_total`, `task_execution_started_total`, and
  `active_workers`.
- `external_payload_used_total` changes label `payload_type` to `payloadType`.
- Canonical `exception` labels are bounded to exception class names. Legacy
  error counters may include raw exception messages.

Legacy metrics that change name or type in canonical mode:

| Legacy metric | Canonical metric | Change |
|---|---|---|
| `task_poll_time` (gauge) | — | Removed; use the histogram instead. |
| `task_execute_time` (gauge) | — | Removed; use the histogram instead. |
| `task_result_size` (gauge) | `task_result_size_bytes` (histogram) | Renamed; gauge becomes histogram with buckets. |
| `workflow_input_size` (gauge) | `workflow_input_size_bytes` (histogram) | Renamed; gauge becomes histogram with buckets. |
| `http_api_client_request` (quantile gauge) | `http_api_client_request_seconds` (histogram) | Renamed with `_seconds` suffix; quantile gauge becomes histogram. |
| `external_payload_used_total{payload_type=…}` | `external_payload_used_total{payloadType=…}` | Label renamed from `payload_type` to `payloadType`. |

Common PromQL replacements:

| Legacy | Canonical |
|---|---|
| `task_poll_time_seconds{quantile="0.95"}` | `histogram_quantile(0.95, sum by (le, taskType, status) (rate(task_poll_time_seconds_bucket[5m])))` |
| `task_execute_time_seconds{quantile="0.95"}` | `histogram_quantile(0.95, sum by (le, taskType, status) (rate(task_execute_time_seconds_bucket[5m])))` |
| `task_update_time_seconds{quantile="0.95"}` | `histogram_quantile(0.95, sum by (le, taskType, status) (rate(task_update_time_seconds_bucket[5m])))` |
| `http_api_client_request{quantile="0.95"}` | `histogram_quantile(0.95, sum by (le, method, uri, status) (rate(http_api_client_request_seconds_bucket[5m])))` |
| `task_result_size` | `task_result_size_bytes_bucket`, `_count`, and `_sum` |
| `workflow_input_size` | `workflow_input_size_bytes_bucket`, `_count`, and `_sum` |
| `external_payload_used_total{payload_type="TASK_OUTPUT"}` | `external_payload_used_total{payloadType="TASK_OUTPUT"}` |

Average latency queries continue to use `_sum` divided by `_count`, but the
canonical series are cumulative histogram counters:

```promql
sum(rate(task_execute_time_seconds_sum[5m])) by (taskType)
/
sum(rate(task_execute_time_seconds_count[5m])) by (taskType)
```

## Troubleshooting

### Metrics Are Empty

- Verify that `metrics_settings` is passed to `TaskHandler`.
- Verify workers have polled or executed tasks. Metrics are created lazily when
  the relevant event occurs.
- Check that the metrics directory is writable.

### Stale or Unexpected Series

- Legacy metrics use the base directory unchanged from prior releases.
  Canonical metrics use a `canonical/` subdirectory, so switching
  implementations never mixes stale metric names.
- Pass `clean_dead_pids=True` to `MetricsSettings` to remove `.db` files from
  PIDs that no longer exist.  Use `clean_directory=True` only when you are sure
  no other live process shares the same directory.
- Restart workers after changing `WORKER_CANONICAL_METRICS`.

### High Cardinality

- Prefer canonical mode for bounded `exception` labels.
- Watch the `uri` label on HTTP metrics. The Python SDK records the request path
  available at the generated API-client call site.
- Avoid embedding user identifiers or unbounded values in task type, workflow
  type, or external payload labels.
