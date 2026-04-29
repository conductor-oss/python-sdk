"""
Legacy Prometheus metrics implementation preserving the metric names, label
conventions, and quantile-gauge timing shape from the original python-sdk.

Events / metrics that have no legacy equivalent are consumed as no-ops.
This class is selected at runtime when WORKER_CANONICAL_METRICS is not true.
"""

from collections import deque
from typing import Any, Dict, List

from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.telemetry import metrics_collector_base as _mcb
from conductor.client.telemetry.metrics_collector_base import MetricsCollectorBase
from conductor.client.telemetry.model.metric_documentation import MetricDocumentation
from conductor.client.telemetry.model.metric_label import MetricLabel
from conductor.client.telemetry.model.metric_name import MetricName


class LegacyMetricsCollector(MetricsCollectorBase):

    QUANTILE_WINDOW_SIZE = 1000

    def __init__(self, settings: MetricsSettings):
        super().__init__(settings)
        self.quantile_metrics: Dict[str, Any] = {}
        self.quantile_data: Dict[str, deque] = {}

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
        pass  # no legacy metric for poll errors

    def increment_task_execution_started(self, task_type: str) -> None:
        pass  # no legacy metric for execution-started

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
            labels={},
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
                MetricLabel.EXCEPTION: str(exception),
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
                MetricLabel.EXCEPTION: str(exception),
            },
        )

    def increment_task_update_error(self, task_type: str, exception) -> None:
        self._increment_counter(
            name=MetricName.TASK_UPDATE_ERROR,
            documentation=MetricDocumentation.TASK_UPDATE_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: str(exception),
            },
        )

    def increment_external_payload_used(self, entity_name: str, operation: str, payload_type: str) -> None:
        self._increment_counter(
            name=MetricName.EXTERNAL_PAYLOAD_USED,
            documentation=MetricDocumentation.EXTERNAL_PAYLOAD_USED,
            labels={
                MetricLabel.ENTITY_NAME: entity_name,
                MetricLabel.OPERATION: operation,
                MetricLabel.PAYLOAD_TYPE_LEGACY: payload_type,
            },
        )

    def increment_workflow_start_error(self, workflow_type: str, exception) -> None:
        self._increment_counter(
            name=MetricName.WORKFLOW_START_ERROR,
            documentation=MetricDocumentation.WORKFLOW_START_ERROR,
            labels={
                MetricLabel.WORKFLOW_TYPE: workflow_type,
                MetricLabel.EXCEPTION: str(exception),
            },
        )

    # ------------------------------------------------------------------
    # Timing (last-value gauges + quantile gauges)
    # ------------------------------------------------------------------

    def record_task_poll_time(self, task_type: str, time_spent: float, status: str = "SUCCESS") -> None:
        self._record_gauge(
            name=MetricName.TASK_POLL_TIME,
            documentation=MetricDocumentation.TASK_POLL_TIME,
            labels={MetricLabel.TASK_TYPE: task_type},
            value=time_spent,
        )
        self._record_quantiles(
            name=MetricName.TASK_POLL_TIME_HISTOGRAM,
            documentation=MetricDocumentation.TASK_POLL_TIME_HISTOGRAM,
            labels={MetricLabel.TASK_TYPE: task_type, MetricLabel.STATUS: status},
            value=time_spent,
        )

    def record_task_execute_time(self, task_type: str, time_spent: float, status: str = "SUCCESS") -> None:
        self._record_gauge(
            name=MetricName.TASK_EXECUTE_TIME,
            documentation=MetricDocumentation.TASK_EXECUTE_TIME,
            labels={MetricLabel.TASK_TYPE: task_type},
            value=time_spent,
        )
        self._record_quantiles(
            name=MetricName.TASK_EXECUTE_TIME_HISTOGRAM,
            documentation=MetricDocumentation.TASK_EXECUTE_TIME_HISTOGRAM,
            labels={MetricLabel.TASK_TYPE: task_type, MetricLabel.STATUS: status},
            value=time_spent,
        )

    def record_task_update_time(self, task_type: str, time_spent: float, status: str = "SUCCESS") -> None:
        self._record_quantiles(
            name=MetricName.TASK_UPDATE_TIME_HISTOGRAM,
            documentation=MetricDocumentation.TASK_UPDATE_TIME_HISTOGRAM,
            labels={MetricLabel.TASK_TYPE: task_type, MetricLabel.STATUS: status},
            value=time_spent,
        )

    def record_api_request_time(self, method: str, uri: str, status: str, time_spent: float) -> None:
        self._record_quantiles(
            name=MetricName.API_REQUEST_TIME,
            documentation=MetricDocumentation.API_REQUEST_TIME,
            labels={
                MetricLabel.METHOD: method,
                MetricLabel.URI: uri,
                MetricLabel.STATUS: status,
            },
            value=time_spent,
        )

    # ------------------------------------------------------------------
    # Sizes (last-value gauges)
    # ------------------------------------------------------------------

    def record_task_result_payload_size(self, task_type: str, payload_size: int) -> None:
        self._record_gauge(
            name=MetricName.TASK_RESULT_SIZE,
            documentation=MetricDocumentation.TASK_RESULT_SIZE,
            labels={MetricLabel.TASK_TYPE: task_type},
            value=payload_size,
        )

    def record_workflow_input_payload_size(self, workflow_type: str, version: str, payload_size: int) -> None:
        self._record_gauge(
            name=MetricName.WORKFLOW_INPUT_SIZE,
            documentation=MetricDocumentation.WORKFLOW_INPUT_SIZE,
            labels={
                MetricLabel.WORKFLOW_TYPE: workflow_type,
                MetricLabel.WORKFLOW_VERSION: version,
            },
            value=payload_size,
        )

    # ------------------------------------------------------------------
    # Quantile-gauge machinery (legacy timing shape)
    # ------------------------------------------------------------------

    def _record_quantiles(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labels: Dict[MetricLabel, str],
            value: float
    ) -> None:
        if not self.must_collect_metrics:
            return

        with self._lock:
            label_values = tuple(labels.values())
            data_key = f"{name}_{label_values}"

            if data_key not in self.quantile_data:
                self.quantile_data[data_key] = deque(maxlen=self.QUANTILE_WINDOW_SIZE)

            self.quantile_data[data_key].append(value)

            observations = sorted(self.quantile_data[data_key])
            n = len(observations)

            if n > 0:
                quantiles = [0.5, 0.75, 0.9, 0.95, 0.99]
                for q in quantiles:
                    quantile_value = self._calculate_quantile(observations, q)
                    gauge = self._get_quantile_gauge(
                        name=name,
                        documentation=documentation,
                        labelnames=[label.value for label in labels.keys()] + ["quantile"],
                    )
                    gauge.labels(*labels.values(), str(q)).set(quantile_value)

                self._update_summary_aggregates(
                    name=name,
                    documentation=documentation,
                    labels=labels,
                    observations=list(self.quantile_data[data_key]),
                )

    @staticmethod
    def _calculate_quantile(sorted_values: List[float], quantile: float) -> float:
        if not sorted_values:
            return 0.0
        n = len(sorted_values)
        index = quantile * (n - 1)
        if index.is_integer():
            return sorted_values[int(index)]
        lower_index = int(index)
        upper_index = min(lower_index + 1, n - 1)
        fraction = index - lower_index
        return sorted_values[lower_index] + fraction * (sorted_values[upper_index] - sorted_values[lower_index])

    def _get_quantile_gauge(self, name, documentation, labelnames):
        if name not in self.quantile_metrics:
            _mcb._ensure_prometheus_imported()
            self.quantile_metrics[name] = _mcb.Gauge(
                name=name,
                documentation=documentation,
                labelnames=labelnames,
                registry=self.registry,
                multiprocess_mode='all',
            )
        return self.quantile_metrics[name]

    def _update_summary_aggregates(self, name, documentation, labels, observations):
        if not observations:
            return
        _mcb._ensure_prometheus_imported()
        base_name = name.value if hasattr(name, 'value') else str(name)
        doc_str = documentation.value if hasattr(documentation, 'value') else str(documentation)

        count_name = f"{base_name}_count"
        if count_name not in self.gauges:
            self.gauges[count_name] = _mcb.Gauge(
                name=count_name,
                documentation=f"{doc_str} - count",
                labelnames=[label.value for label in labels.keys()],
                registry=self.registry,
                multiprocess_mode='all',
            )

        sum_name = f"{base_name}_sum"
        if sum_name not in self.gauges:
            self.gauges[sum_name] = _mcb.Gauge(
                name=sum_name,
                documentation=f"{doc_str} - sum",
                labelnames=[label.value for label in labels.keys()],
                registry=self.registry,
                multiprocess_mode='all',
            )

        self.gauges[count_name].labels(*labels.values()).set(len(observations))
        self.gauges[sum_name].labels(*labels.values()).set(sum(observations))
