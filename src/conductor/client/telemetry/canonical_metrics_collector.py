"""
Canonical Prometheus metrics implementation following the harmonized metric
catalog (see sdk-metrics-harmonization.md).

Uses real Prometheus Histograms for timing and size metrics, bounded-cardinality
exception labels, and canonical metric names (_total suffixed counters, _seconds
suffixed time histograms, _bytes suffixed size histograms).

Events / metrics that have no canonical equivalent (legacy-only gauges) are
consumed as no-ops.  This class is selected at runtime when
WORKER_CANONICAL_METRICS=true.
"""

from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.telemetry.metrics_collector_base import (
    MetricsCollectorBase,
    _exception_label,
)
from conductor.client.telemetry.model.metric_documentation import MetricDocumentation
from conductor.client.telemetry.model.metric_label import MetricLabel
from conductor.client.telemetry.model.metric_name import MetricName

TIME_BUCKETS = (0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
SIZE_BUCKETS = (100, 1_000, 10_000, 100_000, 1_000_000, 10_000_000)


class CanonicalMetricsCollector(MetricsCollectorBase):

    def __init__(self, settings: MetricsSettings):
        super().__init__(settings)

    def collector_name(self) -> str:
        return "canonical"

    # ------------------------------------------------------------------
    # Counters
    # ------------------------------------------------------------------

    def increment_task_poll(self, task_type: str) -> None:
        self._increment_counter(
            name=MetricName.TASK_POLL,
            documentation=MetricDocumentation.TASK_POLL,
            labels={MetricLabel.TASK_TYPE: task_type},
        )

    def increment_task_poll_error(self, task_type: str, exception) -> None:
        self._increment_counter(
            name=MetricName.TASK_POLL_ERROR,
            documentation=MetricDocumentation.TASK_POLL_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: _exception_label(exception),
            },
        )

    def increment_task_execution_started(self, task_type: str) -> None:
        self._increment_counter(
            name=MetricName.TASK_EXECUTION_STARTED,
            documentation=MetricDocumentation.TASK_EXECUTION_STARTED,
            labels={MetricLabel.TASK_TYPE: task_type},
        )

    def increment_task_execution_queue_full(self, task_type: str) -> None:
        self._increment_counter(
            name=MetricName.TASK_EXECUTION_QUEUE_FULL,
            documentation=MetricDocumentation.TASK_EXECUTION_QUEUE_FULL,
            labels={MetricLabel.TASK_TYPE: task_type},
        )

    def increment_uncaught_exception(self, exception=None) -> None:
        self._increment_counter(
            name=MetricName.THREAD_UNCAUGHT_EXCEPTION,
            documentation=MetricDocumentation.THREAD_UNCAUGHT_EXCEPTION,
            labels={
                MetricLabel.EXCEPTION: _exception_label(exception),
            },
        )

    def increment_worker_restart(self, task_type: str) -> None:
        self._increment_counter(
            name=MetricName.WORKER_RESTART,
            documentation=MetricDocumentation.WORKER_RESTART,
            labels={MetricLabel.TASK_TYPE: task_type},
        )

    def increment_task_paused(self, task_type: str) -> None:
        self._increment_counter(
            name=MetricName.TASK_PAUSED,
            documentation=MetricDocumentation.TASK_PAUSED,
            labels={MetricLabel.TASK_TYPE: task_type},
        )

    def increment_task_execution_error(self, task_type: str, exception) -> None:
        self._increment_counter(
            name=MetricName.TASK_EXECUTE_ERROR,
            documentation=MetricDocumentation.TASK_EXECUTE_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: _exception_label(exception),
            },
        )

    def increment_task_ack_failed(self, task_type: str) -> None:
        self._increment_counter(
            name=MetricName.TASK_ACK_FAILED,
            documentation=MetricDocumentation.TASK_ACK_FAILED,
            labels={MetricLabel.TASK_TYPE: task_type},
        )

    def increment_task_ack_error(self, task_type: str, exception) -> None:
        self._increment_counter(
            name=MetricName.TASK_ACK_ERROR,
            documentation=MetricDocumentation.TASK_ACK_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: _exception_label(exception),
            },
        )

    def increment_task_update_error(self, task_type: str, exception) -> None:
        self._increment_counter(
            name=MetricName.TASK_UPDATE_ERROR,
            documentation=MetricDocumentation.TASK_UPDATE_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: _exception_label(exception),
            },
        )

    def increment_external_payload_used(self, entity_name: str, operation: str, payload_type: str) -> None:
        self._increment_counter(
            name=MetricName.EXTERNAL_PAYLOAD_USED,
            documentation=MetricDocumentation.EXTERNAL_PAYLOAD_USED,
            labels={
                MetricLabel.ENTITY_NAME: entity_name,
                MetricLabel.OPERATION: operation,
                MetricLabel.PAYLOAD_TYPE_CAMEL: payload_type,
            },
        )

    def increment_workflow_start_error(self, workflow_type: str, exception) -> None:
        self._increment_counter(
            name=MetricName.WORKFLOW_START_ERROR,
            documentation=MetricDocumentation.WORKFLOW_START_ERROR,
            labels={
                MetricLabel.WORKFLOW_TYPE: workflow_type,
                MetricLabel.EXCEPTION: _exception_label(exception),
            },
        )

    # ------------------------------------------------------------------
    # Gauges
    # ------------------------------------------------------------------

    def set_active_workers(self, task_type: str, count: int) -> None:
        self._record_gauge(
            name=MetricName.ACTIVE_WORKERS,
            documentation=MetricDocumentation.ACTIVE_WORKERS,
            labels={MetricLabel.TASK_TYPE: task_type},
            value=count,
            multiprocess_mode='livesum',
        )

    # ------------------------------------------------------------------
    # Timing (real Prometheus Histograms)
    # ------------------------------------------------------------------

    def record_task_poll_time(self, task_type: str, time_spent: float, status: str = "SUCCESS") -> None:
        self._observe_histogram(
            name=MetricName.TASK_POLL_TIME_HISTOGRAM,
            documentation=MetricDocumentation.TASK_POLL_TIME_HISTOGRAM,
            labels={MetricLabel.TASK_TYPE: task_type, MetricLabel.STATUS: status},
            value=time_spent,
            buckets=TIME_BUCKETS,
        )

    def record_task_execute_time(self, task_type: str, time_spent: float, status: str = "SUCCESS") -> None:
        self._observe_histogram(
            name=MetricName.TASK_EXECUTE_TIME_HISTOGRAM,
            documentation=MetricDocumentation.TASK_EXECUTE_TIME_HISTOGRAM,
            labels={MetricLabel.TASK_TYPE: task_type, MetricLabel.STATUS: status},
            value=time_spent,
            buckets=TIME_BUCKETS,
        )

    def record_task_update_time(self, task_type: str, time_spent: float, status: str = "SUCCESS") -> None:
        self._observe_histogram(
            name=MetricName.TASK_UPDATE_TIME_HISTOGRAM,
            documentation=MetricDocumentation.TASK_UPDATE_TIME_HISTOGRAM,
            labels={MetricLabel.TASK_TYPE: task_type, MetricLabel.STATUS: status},
            value=time_spent,
            buckets=TIME_BUCKETS,
        )

    def record_api_request_time(self, method: str, uri: str, status: str, time_spent: float,
                                metric_uri: str = None) -> None:
        self._observe_histogram(
            name=MetricName.API_REQUEST_TIME_CANONICAL,
            documentation=MetricDocumentation.API_REQUEST_TIME_CANONICAL,
            labels={
                MetricLabel.METHOD: method,
                MetricLabel.URI: metric_uri or uri,
                MetricLabel.STATUS: status,
            },
            value=time_spent,
            buckets=TIME_BUCKETS,
        )

    # ------------------------------------------------------------------
    # Sizes (real Prometheus Histograms with size buckets)
    # ------------------------------------------------------------------

    def record_task_result_payload_size(self, task_type: str, payload_size: int) -> None:
        self._observe_histogram(
            name=MetricName.TASK_RESULT_SIZE_BYTES,
            documentation=MetricDocumentation.TASK_RESULT_SIZE_BYTES,
            labels={MetricLabel.TASK_TYPE: task_type},
            value=payload_size,
            buckets=SIZE_BUCKETS,
        )

    def record_workflow_input_payload_size(self, workflow_type: str, version: str, payload_size: int) -> None:
        self._observe_histogram(
            name=MetricName.WORKFLOW_INPUT_SIZE_BYTES,
            documentation=MetricDocumentation.WORKFLOW_INPUT_SIZE_BYTES,
            labels={
                MetricLabel.WORKFLOW_TYPE: workflow_type,
                MetricLabel.WORKFLOW_VERSION: version,
            },
            value=payload_size,
            buckets=SIZE_BUCKETS,
        )

    # ------------------------------------------------------------------
    # Workflow-client hooks (canonical-only)
    # ------------------------------------------------------------------

    def measure_workflow_input_payload_size(self, name: str, version, workflow_input) -> None:
        import json
        try:
            encoded = json.dumps(workflow_input if workflow_input is not None else {}, default=str)
            size_bytes = len(encoded.encode("utf-8"))
            self.record_workflow_input_payload_size(
                name, str(version) if version is not None else "", size_bytes,
            )
        except Exception:
            pass

    def measure_workflow_start_error(self, name: str, exception: Exception) -> None:
        self.increment_workflow_start_error(name, exception)
