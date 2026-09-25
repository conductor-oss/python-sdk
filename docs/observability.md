# Metrics and logging

Use SDK logging and the metrics collectors to observe polling, task execution,
workflow latency, retries, and failures. Configure log level with
`CONDUCTOR_LOG_LEVEL`; use `METRICS.md` for metric names and Prometheus setup.

For agent executions, inspect the shared workflow record for inputs, outputs, tool
calls, retries, and status. Avoid logging credentials or unredacted sensitive data.
