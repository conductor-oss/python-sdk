# Metrics Documentation

The Conductor Python SDK includes built-in metrics collection using Prometheus to monitor worker performance, API requests, and task execution.

## Table of Contents

- [Quick Reference](#quick-reference)
- [Configuration](#configuration)
- [Metric Types](#metric-types)
- [Examples](#examples)

## Quick Reference

| Metric Name | Type | Labels | Description |
|------------|------|--------|-------------|
| `api_request_time_seconds` | Timer (quantile gauge) | `method`, `uri`, `status`, `quantile` | API request latency to Conductor server |
| `api_request_time_seconds_count` | Gauge | `method`, `uri`, `status` | Total number of API requests |
| `api_request_time_seconds_sum` | Gauge | `method`, `uri`, `status` | Total time spent in API requests |
| `task_poll_total` | Counter | `taskType` | Number of task poll attempts |
| `task_poll_time` | Gauge | `taskType` | Most recent poll duration (legacy) |
| `task_poll_time_seconds` | Timer (quantile gauge) | `taskType`, `status`, `quantile` | Task poll latency distribution |
| `task_poll_time_seconds_count` | Gauge | `taskType`, `status` | Total number of poll attempts by status |
| `task_poll_time_seconds_sum` | Gauge | `taskType`, `status` | Total time spent polling |
| `task_execute_time` | Gauge | `taskType` | Most recent execution duration (legacy) |
| `task_execute_time_seconds` | Timer (quantile gauge) | `taskType`, `status`, `quantile` | Task execution latency distribution |
| `task_execute_time_seconds_count` | Gauge | `taskType`, `status` | Total number of task executions by status |
| `task_execute_time_seconds_sum` | Gauge | `taskType`, `status` | Total time spent executing tasks |
| `task_execute_error_total` | Counter | `taskType`, `exception` | Number of task execution errors |
| `task_update_time_seconds` | Timer (quantile gauge) | `taskType`, `status`, `quantile` | Task update latency distribution |
| `task_update_time_seconds_count` | Gauge | `taskType`, `status` | Total number of task updates by status |
| `task_update_time_seconds_sum` | Gauge | `taskType`, `status` | Total time spent updating tasks |
| `task_update_error_total` | Counter | `taskType`, `exception` | Number of task update errors |
| `task_result_size` | Gauge | `taskType` | Size of task result payload (bytes) |
| `task_execution_queue_full_total` | Counter | `taskType` | Number of times execution queue was full |
| `task_paused_total` | Counter | `taskType` | Number of polls while worker paused |
| `worker_restart_total` | Counter | `taskType` | Number of times TaskHandler restarted a worker subprocess |
| `external_payload_used_total` | Counter | `taskType`, `payloadType` | External payload storage usage count |
| `workflow_input_size` | Gauge | `workflowType`, `version` | Workflow input payload size (bytes) |
| `workflow_start_error_total` | Counter | `workflowType`, `exception` | Workflow start error count |

### Label Values

**`status`**: `SUCCESS`, `FAILURE`
**`method`**: `GET`, `POST`, `PUT`, `DELETE`
**`uri`**: API endpoint path (e.g., `/tasks/poll/batch/{taskType}`, `/tasks/update-v2`)
**`status` (HTTP)**: HTTP response code (`200`, `401`, `404`, `500`) or `error`
**`quantile`**: `0.5` (p50), `0.75` (p75), `0.9` (p90), `0.95` (p95), `0.99` (p99)
**`payloadType`**: `input`, `output`
**`exception`**: Exception type or error message

### Example Metrics Output

```prometheus
# API Request Metrics
api_request_time_seconds{method="GET",uri="/tasks/poll/batch/myTask",status="200",quantile="0.5"} 0.112
api_request_time_seconds{method="GET",uri="/tasks/poll/batch/myTask",status="200",quantile="0.99"} 0.245
api_request_time_seconds_count{method="GET",uri="/tasks/poll/batch/myTask",status="200"} 1000.0
api_request_time_seconds_sum{method="GET",uri="/tasks/poll/batch/myTask",status="200"} 114.5

# Task Poll Metrics
task_poll_total{taskType="myTask"} 10264.0
task_poll_time_seconds{taskType="myTask",status="SUCCESS",quantile="0.95"} 0.025
task_poll_time_seconds_count{taskType="myTask",status="SUCCESS"} 1000.0
task_poll_time_seconds_count{taskType="myTask",status="FAILURE"} 95.0

# Task Execution Metrics
task_execute_time_seconds{taskType="myTask",status="SUCCESS",quantile="0.99"} 0.017
task_execute_time_seconds_count{taskType="myTask",status="SUCCESS"} 120.0
task_execute_error_total{taskType="myTask",exception="TimeoutError"} 3.0

# Task Update Metrics
task_update_time_seconds{taskType="myTask",status="SUCCESS",quantile="0.95"} 0.096
task_update_time_seconds_count{taskType="myTask",status="SUCCESS"} 15.0
```

## Configuration

### Enabling Metrics

Metrics are enabled by providing a `MetricsSettings` object when creating a `TaskHandler`:

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.automator.task_handler import TaskHandler

# Configure metrics
metrics_settings = MetricsSettings(
    directory='/path/to/metrics',       # Directory where metrics file will be written
    file_name='conductor_metrics.prom', # Metrics file name (default: 'conductor_metrics.prom')
    update_interval=10                  # Update interval in seconds (default: 10)
)

# Configure Conductor connection
api_config = Configuration(
    server_api_url='http://localhost:8080/api',
    debug=False
)

# Create task handler with metrics
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

### Quantile Gauges (Timers)

All timing metrics use quantile gauges to track latency distribution:

- **Quantile labels**: Each metric includes 5 quantiles (p50, p75, p90, p95, p99)
- **Count suffix**: `{metric_name}_count` tracks total number of observations
- **Sum suffix**: `{metric_name}_sum` tracks total time spent

**Example calculation (average):**
```
average = task_poll_time_seconds_sum / task_poll_time_seconds_count
average = 18.75 / 1000.0 = 0.01875 seconds
```

**Why quantiles instead of histograms?**
- More accurate percentile tracking with sliding window (last 1000 observations)
- No need to pre-configure bucket boundaries
- Lower memory footprint
- Direct percentile values without interpolation

### Sliding Window

Quantile metrics use a sliding window of the last 1000 observations to calculate percentiles. This provides:
- Recent performance data (not cumulative)
- Accurate percentile estimation
- Bounded memory usage

## Examples

### Querying Metrics with PromQL

**Average API request latency:**
```promql
rate(api_request_time_seconds_sum[5m]) / rate(api_request_time_seconds_count[5m])
```

**API error rate:**
```promql
sum(rate(api_request_time_seconds_count{status=~"4..|5.."}[5m]))
/
sum(rate(api_request_time_seconds_count[5m]))
```

**Task poll success rate:**
```promql
sum(rate(task_poll_time_seconds_count{status="SUCCESS"}[5m]))
/
sum(rate(task_poll_time_seconds_count[5m]))
```

**p95 task execution time:**
```promql
task_execute_time_seconds{quantile="0.95"}
```

**Slowest API endpoints (p99):**
```promql
topk(10, api_request_time_seconds{quantile="0.99"})
```

### Complete Example

```python
import os
import shutil
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.worker.worker_interface import WorkerInterface

# Clean metrics directory
metrics_dir = os.path.join(os.path.expanduser('~'), 'conductor_metrics')
if os.path.exists(metrics_dir):
    shutil.rmtree(metrics_dir)
os.makedirs(metrics_dir, exist_ok=True)

# Configure metrics
metrics_settings = MetricsSettings(
    directory=metrics_dir,
    file_name='conductor_metrics.prom',
    update_interval=10  # Update file every 10 seconds
)

# Configure Conductor
api_config = Configuration(
    server_api_url='http://localhost:8080/api',
    debug=False
)

# Define worker
class MyWorker(WorkerInterface):
    def execute(self, task):
        return {'status': 'completed'}

    def get_task_definition_name(self):
        return 'my_task'

# Start with metrics
with TaskHandler(
    configuration=api_config,
    metrics_settings=metrics_settings,
    workers=[MyWorker()]
) as task_handler:
    task_handler.start_processes()
```

### Scraping with Prometheus

Configure Prometheus to scrape the metrics file:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'conductor-python-sdk'
    static_configs:
      - targets: ['localhost:8000']  # Use file_sd or custom exporter
    metric_relabel_configs:
      - source_labels: [taskType]
        target_label: task_type
```

**Note:** Since metrics are written to a file, you'll need to either:
1. Use Prometheus's `textfile` collector with Node Exporter
2. Create a simple HTTP server to expose the metrics file
3. Use a custom exporter to read and serve the file

### Example HTTP Metrics Server

```python
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class MetricsHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            metrics_file = '/path/to/conductor_metrics.prom'
            if os.path.exists(metrics_file):
                with open(metrics_file, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; version=0.0.4')
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

# Run server
httpd = HTTPServer(('0.0.0.0', 8000), MetricsHandler)
httpd.serve_forever()
```

## Best Practices

1. **Clean metrics directory on startup** to avoid stale multiprocess metrics
2. **Monitor disk space** as metrics files can grow with many task types
3. **Use appropriate update_interval** (10-60 seconds recommended)
4. **Set up alerts** on error rates and high latencies
5. **Monitor queue saturation** (`task_execution_queue_full_total`) for backpressure
6. **Track API errors** by status code to identify authentication or server issues
7. **Use p95/p99 latencies** for SLO monitoring rather than averages

## Troubleshooting

### Metrics file is empty
- Ensure `MetricsCollector` is registered as an event listener
- Check that workers are actually polling and executing tasks
- Verify the metrics directory has write permissions

### Stale metrics after restart
- Clean the metrics directory on startup (see Configuration section)
- Prometheus's `multiprocess` mode requires cleanup between runs

### High memory usage
- Reduce the sliding window size (default: 1000 observations)
- Increase `update_interval` to write less frequently
- Limit the number of unique label combinations

### Missing metrics
- Verify `metrics_settings` is passed to TaskHandler
- Check that the SDK version supports the metric you're looking for
- Ensure workers are properly registered and running
