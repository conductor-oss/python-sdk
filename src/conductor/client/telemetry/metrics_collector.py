import logging
import os
import time
from collections import deque
from typing import Any, ClassVar, Dict, List, Tuple

from prometheus_client import CollectorRegistry
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import Histogram
from prometheus_client import Summary
from prometheus_client import write_to_textfile
from prometheus_client.multiprocess import MultiProcessCollector

from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.telemetry.model.metric_documentation import MetricDocumentation
from conductor.client.telemetry.model.metric_label import MetricLabel
from conductor.client.telemetry.model.metric_name import MetricName

# Event system imports (for new event-driven architecture)
from conductor.client.event.task_runner_events import (
    PollStarted,
    PollCompleted,
    PollFailure,
    TaskExecutionStarted,
    TaskExecutionCompleted,
    TaskExecutionFailure,
)
from conductor.client.event.workflow_events import (
    WorkflowStarted,
    WorkflowInputPayloadSize,
    WorkflowPayloadUsed,
)
from conductor.client.event.task_events import (
    TaskResultPayloadSize,
    TaskPayloadUsed,
)

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)


class MetricsCollector:
    """
    Prometheus-based metrics collector for Conductor operations.

    This class implements the event listener protocols (TaskRunnerEventsListener,
    WorkflowEventsListener, TaskEventsListener) via structural subtyping (duck typing),
    matching the Java SDK's MetricsCollector interface.

    Supports both usage patterns:
    1. Direct method calls (backward compatible):
       metrics.increment_task_poll(task_type)

    2. Event-driven (new):
       dispatcher.register(PollStarted, metrics.on_poll_started)
       dispatcher.publish(PollStarted(...))

    Note: Uses Python's Protocol for structural subtyping rather than explicit
    inheritance to avoid circular imports and maintain backward compatibility.
    """
    counters: ClassVar[Dict[str, Counter]] = {}
    gauges: ClassVar[Dict[str, Gauge]] = {}
    histograms: ClassVar[Dict[str, Histogram]] = {}
    summaries: ClassVar[Dict[str, Summary]] = {}
    quantile_metrics: ClassVar[Dict[str, Gauge]] = {}  # metric_name -> Gauge with quantile label (used as summary)
    quantile_data: ClassVar[Dict[str, deque]] = {}  # metric_name+labels -> deque of values
    registry = CollectorRegistry()
    must_collect_metrics = False
    QUANTILE_WINDOW_SIZE = 1000  # Keep last 1000 observations for quantile calculation

    def __init__(self, settings: MetricsSettings):
        if settings is not None:
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = settings.directory
            MultiProcessCollector(self.registry)
            self.must_collect_metrics = True

    @staticmethod
    def provide_metrics(settings: MetricsSettings) -> None:
        if settings is None:
            return
        OUTPUT_FILE_PATH = os.path.join(
            settings.directory,
            settings.file_name
        )
        registry = CollectorRegistry()
        MultiProcessCollector(registry)
        while True:
            write_to_textfile(
                OUTPUT_FILE_PATH,
                registry
            )
            time.sleep(settings.update_interval)

    def increment_task_poll(self, task_type: str) -> None:
        self.__increment_counter(
            name=MetricName.TASK_POLL,
            documentation=MetricDocumentation.TASK_POLL,
            labels={
                MetricLabel.TASK_TYPE: task_type
            }
        )

    def increment_task_execution_queue_full(self, task_type: str) -> None:
        self.__increment_counter(
            name=MetricName.TASK_EXECUTION_QUEUE_FULL,
            documentation=MetricDocumentation.TASK_EXECUTION_QUEUE_FULL,
            labels={
                MetricLabel.TASK_TYPE: task_type
            }
        )

    def increment_uncaught_exception(self):
        self.__increment_counter(
            name=MetricName.THREAD_UNCAUGHT_EXCEPTION,
            documentation=MetricDocumentation.THREAD_UNCAUGHT_EXCEPTION,
            labels={}
        )

    def increment_task_poll_error(self, task_type: str, exception: Exception) -> None:
        # No-op: Poll errors are already tracked via task_poll_time_seconds_count with status=FAILURE
        pass

    def increment_task_paused(self, task_type: str) -> None:
        self.__increment_counter(
            name=MetricName.TASK_PAUSED,
            documentation=MetricDocumentation.TASK_PAUSED,
            labels={
                MetricLabel.TASK_TYPE: task_type
            }
        )

    def increment_task_execution_error(self, task_type: str, exception: Exception) -> None:
        self.__increment_counter(
            name=MetricName.TASK_EXECUTE_ERROR,
            documentation=MetricDocumentation.TASK_EXECUTE_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: str(exception)
            }
        )

    def increment_task_ack_failed(self, task_type: str) -> None:
        self.__increment_counter(
            name=MetricName.TASK_ACK_FAILED,
            documentation=MetricDocumentation.TASK_ACK_FAILED,
            labels={
                MetricLabel.TASK_TYPE: task_type
            }
        )

    def increment_task_ack_error(self, task_type: str, exception: Exception) -> None:
        self.__increment_counter(
            name=MetricName.TASK_ACK_ERROR,
            documentation=MetricDocumentation.TASK_ACK_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: str(exception)
            }
        )

    def increment_task_update_error(self, task_type: str, exception: Exception) -> None:
        self.__increment_counter(
            name=MetricName.TASK_UPDATE_ERROR,
            documentation=MetricDocumentation.TASK_UPDATE_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: str(exception)
            }
        )

    def increment_external_payload_used(self, entity_name: str, operation: str, payload_type: str) -> None:
        self.__increment_counter(
            name=MetricName.EXTERNAL_PAYLOAD_USED,
            documentation=MetricDocumentation.EXTERNAL_PAYLOAD_USED,
            labels={
                MetricLabel.ENTITY_NAME: entity_name,
                MetricLabel.OPERATION: operation,
                MetricLabel.PAYLOAD_TYPE: payload_type
            }
        )

    def increment_workflow_start_error(self, workflow_type: str, exception: Exception) -> None:
        self.__increment_counter(
            name=MetricName.WORKFLOW_START_ERROR,
            documentation=MetricDocumentation.WORKFLOW_START_ERROR,
            labels={
                MetricLabel.WORKFLOW_TYPE: workflow_type,
                MetricLabel.EXCEPTION: str(exception)
            }
        )

    def record_workflow_input_payload_size(self, workflow_type: str, version: str, payload_size: int) -> None:
        self.__record_gauge(
            name=MetricName.WORKFLOW_INPUT_SIZE,
            documentation=MetricDocumentation.WORKFLOW_INPUT_SIZE,
            labels={
                MetricLabel.WORKFLOW_TYPE: workflow_type,
                MetricLabel.WORKFLOW_VERSION: version
            },
            value=payload_size
        )

    def record_task_result_payload_size(self, task_type: str, payload_size: int) -> None:
        self.__record_gauge(
            name=MetricName.TASK_RESULT_SIZE,
            documentation=MetricDocumentation.TASK_RESULT_SIZE,
            labels={
                MetricLabel.TASK_TYPE: task_type
            },
            value=payload_size
        )

    def record_task_poll_time(self, task_type: str, time_spent: float, status: str = "SUCCESS") -> None:
        self.__record_gauge(
            name=MetricName.TASK_POLL_TIME,
            documentation=MetricDocumentation.TASK_POLL_TIME,
            labels={
                MetricLabel.TASK_TYPE: task_type
            },
            value=time_spent
        )
        # Record as quantile gauges for percentile tracking
        self.__record_quantiles(
            name=MetricName.TASK_POLL_TIME_HISTOGRAM,
            documentation=MetricDocumentation.TASK_POLL_TIME_HISTOGRAM,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.STATUS: status
            },
            value=time_spent
        )

    def record_task_execute_time(self, task_type: str, time_spent: float, status: str = "SUCCESS") -> None:
        self.__record_gauge(
            name=MetricName.TASK_EXECUTE_TIME,
            documentation=MetricDocumentation.TASK_EXECUTE_TIME,
            labels={
                MetricLabel.TASK_TYPE: task_type
            },
            value=time_spent
        )
        # Record as quantile gauges for percentile tracking
        self.__record_quantiles(
            name=MetricName.TASK_EXECUTE_TIME_HISTOGRAM,
            documentation=MetricDocumentation.TASK_EXECUTE_TIME_HISTOGRAM,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.STATUS: status
            },
            value=time_spent
        )

    def record_task_poll_time_histogram(self, task_type: str, time_spent: float, status: str = "SUCCESS") -> None:
        """Record task poll time with quantile gauges for percentile tracking."""
        self.__record_quantiles(
            name=MetricName.TASK_POLL_TIME_HISTOGRAM,
            documentation=MetricDocumentation.TASK_POLL_TIME_HISTOGRAM,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.STATUS: status
            },
            value=time_spent
        )

    def record_task_execute_time_histogram(self, task_type: str, time_spent: float, status: str = "SUCCESS") -> None:
        """Record task execution time with quantile gauges for percentile tracking."""
        self.__record_quantiles(
            name=MetricName.TASK_EXECUTE_TIME_HISTOGRAM,
            documentation=MetricDocumentation.TASK_EXECUTE_TIME_HISTOGRAM,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.STATUS: status
            },
            value=time_spent
        )

    def record_task_update_time_histogram(self, task_type: str, time_spent: float, status: str = "SUCCESS") -> None:
        """Record task update time with quantile gauges for percentile tracking."""
        self.__record_quantiles(
            name=MetricName.TASK_UPDATE_TIME_HISTOGRAM,
            documentation=MetricDocumentation.TASK_UPDATE_TIME_HISTOGRAM,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.STATUS: status
            },
            value=time_spent
        )

    def record_api_request_time(self, method: str, uri: str, status: str, time_spent: float) -> None:
        """Record API request time with quantile gauges for percentile tracking."""
        self.__record_quantiles(
            name=MetricName.API_REQUEST_TIME,
            documentation=MetricDocumentation.API_REQUEST_TIME,
            labels={
                MetricLabel.METHOD: method,
                MetricLabel.URI: uri,
                MetricLabel.STATUS: status
            },
            value=time_spent
        )

    def __increment_counter(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labels: Dict[MetricLabel, str]
    ) -> None:
        if not self.must_collect_metrics:
            return
        counter = self.__get_counter(
            name=name,
            documentation=documentation,
            labelnames=[label.value for label in labels.keys()]
        )
        counter.labels(*labels.values()).inc()

    def __record_gauge(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labels: Dict[MetricLabel, str],
            value: Any
    ) -> None:
        if not self.must_collect_metrics:
            return
        gauge = self.__get_gauge(
            name=name,
            documentation=documentation,
            labelnames=[label.value for label in labels.keys()]
        )
        gauge.labels(*labels.values()).set(value)

    def __get_counter(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labelnames: List[MetricLabel]
    ) -> Counter:
        if name not in self.counters:
            self.counters[name] = self.__generate_counter(
                name, documentation, labelnames
            )
        return self.counters[name]

    def __get_gauge(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labelnames: List[MetricLabel]
    ) -> Gauge:
        if name not in self.gauges:
            self.gauges[name] = self.__generate_gauge(
                name, documentation, labelnames
            )
        return self.gauges[name]

    def __generate_counter(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labelnames: List[MetricLabel]
    ) -> Counter:
        return Counter(
            name=name,
            documentation=documentation,
            labelnames=labelnames,
            registry=self.registry
        )

    def __generate_gauge(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labelnames: List[MetricLabel]
    ) -> Gauge:
        return Gauge(
            name=name,
            documentation=documentation,
            labelnames=labelnames,
            registry=self.registry
        )

    def __observe_histogram(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labels: Dict[MetricLabel, str],
            value: Any
    ) -> None:
        if not self.must_collect_metrics:
            return
        histogram = self.__get_histogram(
            name=name,
            documentation=documentation,
            labelnames=[label.value for label in labels.keys()]
        )
        histogram.labels(*labels.values()).observe(value)

    def __get_histogram(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labelnames: List[MetricLabel]
    ) -> Histogram:
        if name not in self.histograms:
            self.histograms[name] = self.__generate_histogram(
                name, documentation, labelnames
            )
        return self.histograms[name]

    def __generate_histogram(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labelnames: List[MetricLabel]
    ) -> Histogram:
        # Standard buckets for timing metrics: 1ms to 10s
        return Histogram(
            name=name,
            documentation=documentation,
            labelnames=labelnames,
            buckets=(0.001, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry
        )

    def __observe_summary(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labels: Dict[MetricLabel, str],
            value: Any
    ) -> None:
        if not self.must_collect_metrics:
            return
        summary = self.__get_summary(
            name=name,
            documentation=documentation,
            labelnames=[label.value for label in labels.keys()]
        )
        summary.labels(*labels.values()).observe(value)

    def __get_summary(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labelnames: List[MetricLabel]
    ) -> Summary:
        if name not in self.summaries:
            self.summaries[name] = self.__generate_summary(
                name, documentation, labelnames
            )
        return self.summaries[name]

    def __generate_summary(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labelnames: List[MetricLabel]
    ) -> Summary:
        # Create summary metric
        # Note: Prometheus Summary metrics provide count and sum by default
        # For percentiles, use histogram buckets or calculate server-side
        return Summary(
            name=name,
            documentation=documentation,
            labelnames=labelnames,
            registry=self.registry
        )

    def __record_quantiles(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labels: Dict[MetricLabel, str],
            value: float
    ) -> None:
        """
        Record a value and update quantile gauges (p50, p75, p90, p95, p99).
        Also maintains _count and _sum for proper summary metrics.

        Maintains a sliding window of observations and calculates quantiles.
        """
        if not self.must_collect_metrics:
            return

        # Create a key for this metric+labels combination
        label_values = tuple(labels.values())
        data_key = f"{name}_{label_values}"

        # Initialize data window if needed
        if data_key not in self.quantile_data:
            self.quantile_data[data_key] = deque(maxlen=self.QUANTILE_WINDOW_SIZE)

        # Add new observation
        self.quantile_data[data_key].append(value)

        # Calculate and update quantiles
        observations = sorted(self.quantile_data[data_key])
        n = len(observations)

        if n > 0:
            quantiles = [0.5, 0.75, 0.9, 0.95, 0.99]
            for q in quantiles:
                quantile_value = self.__calculate_quantile(observations, q)

                # Get or create gauge for this quantile
                gauge = self.__get_quantile_gauge(
                    name=name,
                    documentation=documentation,
                    labelnames=[label.value for label in labels.keys()] + ["quantile"],
                    quantile=q
                )

                # Set gauge value with labels + quantile
                gauge.labels(*labels.values(), str(q)).set(quantile_value)

            # Also publish _count and _sum for proper summary metrics
            self.__update_summary_aggregates(
                name=name,
                documentation=documentation,
                labels=labels,
                observations=list(self.quantile_data[data_key])
            )

    def __calculate_quantile(self, sorted_values: List[float], quantile: float) -> float:
        """Calculate quantile from sorted list of values."""
        if not sorted_values:
            return 0.0

        n = len(sorted_values)
        index = quantile * (n - 1)

        if index.is_integer():
            return sorted_values[int(index)]
        else:
            # Linear interpolation
            lower_index = int(index)
            upper_index = min(lower_index + 1, n - 1)
            fraction = index - lower_index
            return sorted_values[lower_index] + fraction * (sorted_values[upper_index] - sorted_values[lower_index])

    def __get_quantile_gauge(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labelnames: List[str],
            quantile: float
    ) -> Gauge:
        """Get or create a gauge for quantiles (single gauge with quantile label)."""
        if name not in self.quantile_metrics:
            # Create a single gauge with quantile as a label
            # This gauge will be shared across all quantiles for this metric
            self.quantile_metrics[name] = Gauge(
                name=name,
                documentation=documentation,
                labelnames=labelnames,
                registry=self.registry
            )

        return self.quantile_metrics[name]

    def __update_summary_aggregates(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labels: Dict[MetricLabel, str],
            observations: List[float]
    ) -> None:
        """
        Update _count and _sum gauges for proper summary metric format.
        This makes the metrics compatible with Prometheus summary type.
        """
        if not observations:
            return

        # Convert enum to string value
        base_name = name.value if hasattr(name, 'value') else str(name)

        # Convert documentation enum to string
        doc_str = documentation.value if hasattr(documentation, 'value') else str(documentation)

        # Get or create _count gauge
        count_name = f"{base_name}_count"
        if count_name not in self.gauges:
            self.gauges[count_name] = Gauge(
                name=count_name,
                documentation=f"{doc_str} - count",
                labelnames=[label.value for label in labels.keys()],
                registry=self.registry
            )

        # Get or create _sum gauge
        sum_name = f"{base_name}_sum"
        if sum_name not in self.gauges:
            self.gauges[sum_name] = Gauge(
                name=sum_name,
                documentation=f"{doc_str} - sum",
                labelnames=[label.value for label in labels.keys()],
                registry=self.registry
            )

        # Update values
        self.gauges[count_name].labels(*labels.values()).set(len(observations))
        self.gauges[sum_name].labels(*labels.values()).set(sum(observations))

    # =========================================================================
    # Event Listener Protocol Implementation (TaskRunnerEventsListener)
    # =========================================================================
    # These methods allow MetricsCollector to be used as an event listener
    # in the new event-driven architecture, while maintaining backward
    # compatibility with existing direct method calls.

    def on_poll_started(self, event: PollStarted) -> None:
        """
        Handle poll started event.
        Maps to increment_task_poll() for backward compatibility.
        """
        self.increment_task_poll(event.task_type)

    def on_poll_completed(self, event: PollCompleted) -> None:
        """
        Handle poll completed event.
        Maps to record_task_poll_time() for backward compatibility.
        """
        self.record_task_poll_time(event.task_type, event.duration_ms / 1000, status="SUCCESS")

    def on_poll_failure(self, event: PollFailure) -> None:
        """
        Handle poll failure event.
        Maps to increment_task_poll_error() for backward compatibility.
        Also records poll time with FAILURE status.
        """
        self.increment_task_poll_error(event.task_type, event.cause)
        # Record poll time with failure status if duration is available
        if hasattr(event, 'duration_ms') and event.duration_ms is not None:
            self.record_task_poll_time(event.task_type, event.duration_ms / 1000, status="FAILURE")

    def on_task_execution_started(self, event: TaskExecutionStarted) -> None:
        """
        Handle task execution started event.
        No direct metric equivalent in old system - could be used for
        tracking in-flight tasks in the future.
        """
        pass  # No corresponding metric in existing system

    def on_task_execution_completed(self, event: TaskExecutionCompleted) -> None:
        """
        Handle task execution completed event.
        Maps to record_task_execute_time() and record_task_result_payload_size().
        """
        self.record_task_execute_time(event.task_type, event.duration_ms / 1000, status="SUCCESS")
        if event.output_size_bytes is not None:
            self.record_task_result_payload_size(event.task_type, event.output_size_bytes)

    def on_task_execution_failure(self, event: TaskExecutionFailure) -> None:
        """
        Handle task execution failure event.
        Maps to increment_task_execution_error() for backward compatibility.
        Also records execution time with FAILURE status.
        """
        self.increment_task_execution_error(event.task_type, event.cause)
        # Record execution time with failure status if duration is available
        if hasattr(event, 'duration_ms') and event.duration_ms is not None:
            self.record_task_execute_time(event.task_type, event.duration_ms / 1000, status="FAILURE")

    # =========================================================================
    # Event Listener Protocol Implementation (WorkflowEventsListener)
    # =========================================================================

    def on_workflow_started(self, event: WorkflowStarted) -> None:
        """
        Handle workflow started event.
        Maps to increment_workflow_start_error() if workflow failed to start.
        """
        if not event.success and event.cause is not None:
            self.increment_workflow_start_error(event.name, event.cause)

    def on_workflow_input_payload_size(self, event: WorkflowInputPayloadSize) -> None:
        """
        Handle workflow input payload size event.
        Maps to record_workflow_input_payload_size().
        """
        version_str = str(event.version) if event.version is not None else "1"
        self.record_workflow_input_payload_size(event.name, version_str, event.size_bytes)

    def on_workflow_payload_used(self, event: WorkflowPayloadUsed) -> None:
        """
        Handle workflow external payload usage event.
        Maps to increment_external_payload_used().
        """
        self.increment_external_payload_used(event.name, event.operation, event.payload_type)

    # =========================================================================
    # Event Listener Protocol Implementation (TaskEventsListener)
    # =========================================================================

    def on_task_result_payload_size(self, event: TaskResultPayloadSize) -> None:
        """
        Handle task result payload size event.
        Maps to record_task_result_payload_size().
        """
        self.record_task_result_payload_size(event.task_type, event.size_bytes)

    def on_task_payload_used(self, event: TaskPayloadUsed) -> None:
        """
        Handle task external payload usage event.
        Maps to increment_external_payload_used().
        """
        self.increment_external_payload_used(event.task_type, event.operation, event.payload_type)
