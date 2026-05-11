import abc
import collections
import logging
import os
import signal
import threading
import time
from typing import Any, Dict, List

# Lazy imports - these will be imported when first needed.
# PROMETHEUS_MULTIPROC_DIR must be set before prometheus_client is imported.
CollectorRegistry = None
Counter = None
Gauge = None
Histogram = None
Summary = None
write_to_textfile = None
MultiProcessCollector = None


def _ensure_prometheus_imported():
    """Lazy import of prometheus_client to ensure PROMETHEUS_MULTIPROC_DIR is set first."""
    global CollectorRegistry, Counter, Gauge, Histogram, Summary, write_to_textfile, MultiProcessCollector

    if CollectorRegistry is None:
        from prometheus_client import CollectorRegistry as _CollectorRegistry
        from prometheus_client import Counter as _Counter
        from prometheus_client import Gauge as _Gauge
        from prometheus_client import Histogram as _Histogram
        from prometheus_client import Summary as _Summary
        from prometheus_client import write_to_textfile as _write_to_textfile
        from prometheus_client.multiprocess import MultiProcessCollector as _MultiProcessCollector

        CollectorRegistry = _CollectorRegistry
        Counter = _Counter
        Gauge = _Gauge
        Histogram = _Histogram
        Summary = _Summary
        write_to_textfile = _write_to_textfile
        MultiProcessCollector = _MultiProcessCollector


def _exception_label(exception) -> str:
    """
    Return a bounded-cardinality label value for an exception.

    Reduces to the bare class name (mirroring the Java / Go SDK convention)
    to prevent unbounded label cardinality from error messages.
    """
    if exception is None:
        return "None"
    if isinstance(exception, type):
        return exception.__name__
    if isinstance(exception, BaseException):
        return type(exception).__name__
    return str(exception)


from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.telemetry.model.metric_documentation import MetricDocumentation
from conductor.client.telemetry.model.metric_label import MetricLabel
from conductor.client.telemetry.model.metric_name import MetricName

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


class MetricsCollectorBase(abc.ABC):
    """
    Abstract base class for Conductor metrics collectors.

    Provides shared Prometheus infrastructure (registry, lazy imports, multiprocess
    aggregation, HTTP server) and concrete event-handler implementations that
    delegate to abstract metric methods.  Subclasses implement the abstract methods
    to emit either legacy or canonical metric shapes.

    Satisfies the MetricsCollector Protocol in event/listeners.py via duck typing.
    """

    def __init__(self, settings: MetricsSettings):
        self.counters: Dict[str, Any] = {}
        self.gauges: Dict[str, Any] = {}
        self.histograms: Dict[str, Any] = {}
        self.summaries: Dict[str, Any] = {}
        self.registry = None
        self.must_collect_metrics = False
        self._lock = threading.RLock()
        self._active_worker_counts: Dict[str, int] = collections.defaultdict(int)

        if settings is None:
            return

        os.environ["PROMETHEUS_MULTIPROC_DIR"] = settings.directory

        _ensure_prometheus_imported()

        self.registry = CollectorRegistry()

        self.must_collect_metrics = True
        logger.debug(
            "MetricsCollector initialized with directory=%s, must_collect=%s",
            settings.directory,
            self.must_collect_metrics,
        )

    # =========================================================================
    # Static: Multiprocess metrics aggregation + HTTP serving
    # =========================================================================

    @staticmethod
    def provide_metrics(settings: MetricsSettings) -> None:
        if settings is None:
            return

        # Ignore SIGINT in this subprocess -- Ctrl-C is handled by the parent
        # via SIGTERM from TaskHandler.stop_processes(). Without this, Ctrl-C
        # produces noisy KeyboardInterrupt tracebacks from time.sleep().
        try:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
        except Exception:
            pass

        os.environ["PROMETHEUS_MULTIPROC_DIR"] = settings.directory

        _ensure_prometheus_imported()

        OUTPUT_FILE_PATH = os.path.join(
            settings.directory,
            settings.file_name
        )

        registry = CollectorRegistry()
        from prometheus_client.multiprocess import MultiProcessCollector as MPCollector
        from prometheus_client.samples import Sample
        from prometheus_client.metrics_core import Metric

        class NoPidCollector(MPCollector):
            """Custom collector that removes pid label and aggregates metrics across processes."""
            def collect(self):
                for metric in super().collect():
                    aggregated = {}

                    for sample in metric.samples:
                        labels = {k: v for k, v in sample.labels.items() if k != 'pid'}
                        label_items = tuple(sorted(labels.items()))
                        key = (sample.name, label_items)

                        if key not in aggregated:
                            aggregated[key] = {
                                'labels': labels,
                                'values': [],
                                'name': sample.name,
                                'timestamp': sample.timestamp,
                                'exemplar': sample.exemplar
                            }

                        aggregated[key]['values'].append(sample.value)

                    filtered_samples = []
                    for key, data in aggregated.items():
                        if metric.type == 'counter' or data['name'].endswith('_count') or data['name'].endswith('_sum'):
                            value = sum(data['values'])
                        elif metric.type == 'histogram' or '_bucket' in data['name']:
                            value = sum(data['values'])
                        elif 'quantile' in data['labels']:
                            value = sum(data['values']) / len(data['values'])
                        else:
                            value = data['values'][-1]

                        filtered_samples.append(
                            Sample(data['name'], data['labels'], value, data['timestamp'], data['exemplar'])
                        )

                    new_metric = Metric(metric.name, metric.documentation, metric.type)
                    new_metric.samples = filtered_samples
                    yield new_metric

        NoPidCollector(registry)

        http_server = None
        if settings.http_port is not None:
            http_server = MetricsCollectorBase._start_http_server(settings.http_port, registry)
            logger.info(f"Metrics HTTP server mode: serving from memory (no file writes) (pid={os.getpid()})")

            while True:
                time.sleep(settings.update_interval)
        else:
            logger.info(f"Metrics file mode: writing to {OUTPUT_FILE_PATH} (pid={os.getpid()})")
            while True:
                try:
                    write_to_textfile(
                        OUTPUT_FILE_PATH,
                        registry
                    )
                except Exception as e:
                    logger.debug(f"Error writing metrics (will retry): {e}")

                time.sleep(settings.update_interval)

    @staticmethod
    def _start_http_server(port: int, registry) -> 'HTTPServer':
        """Start HTTP server to expose metrics endpoint for Prometheus scraping."""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading as _threading

        class MetricsHTTPHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/metrics':
                    try:
                        from prometheus_client import generate_latest
                        metrics_content = generate_latest(registry)

                        self.send_response(200)
                        self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(metrics_content)

                    except Exception as e:
                        logger.error(f"Error serving metrics: {e}")
                        self.send_response(500)
                        self.send_header('Content-Type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(f'Error: {str(e)}'.encode('utf-8'))

                elif self.path == '/' or self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'OK')

                else:
                    self.send_response(404)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Not Found - Try /metrics')

            def log_message(self, format, *args):
                logger.debug(f"HTTP {self.address_string()} - {format % args}")

        server = HTTPServer(('', port), MetricsHTTPHandler)
        logger.info(f"Started metrics HTTP server on port {port} (pid={os.getpid()})")
        logger.info(f"Metrics available at: http://localhost:{port}/metrics")

        server_thread = _threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        return server

    # =========================================================================
    # Shared Prometheus helpers (used by subclasses)
    # =========================================================================

    def _increment_counter(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labels: Dict[MetricLabel, str]
    ) -> None:
        if not self.must_collect_metrics:
            return
        with self._lock:
            counter = self._get_counter(
                name=name,
                documentation=documentation,
                labelnames=[label.value for label in labels.keys()]
            )
            counter.labels(*labels.values()).inc()

    def _record_gauge(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labels: Dict[MetricLabel, str],
            value: Any
    ) -> None:
        if not self.must_collect_metrics:
            return
        with self._lock:
            gauge = self._get_gauge(
                name=name,
                documentation=documentation,
                labelnames=[label.value for label in labels.keys()]
            )
            gauge.labels(*labels.values()).set(value)

    def _observe_histogram(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labels: Dict[MetricLabel, str],
            value: Any,
            buckets=None
    ) -> None:
        if not self.must_collect_metrics:
            return
        with self._lock:
            histogram = self._get_histogram(
                name=name,
                documentation=documentation,
                labelnames=[label.value for label in labels.keys()],
                buckets=buckets
            )
            histogram.labels(*labels.values()).observe(value)

    def _get_counter(self, name, documentation, labelnames):
        if name not in self.counters:
            self.counters[name] = Counter(
                name=name,
                documentation=documentation,
                labelnames=labelnames,
                registry=self.registry
            )
        return self.counters[name]

    def _get_gauge(self, name, documentation, labelnames):
        if name not in self.gauges:
            self.gauges[name] = Gauge(
                name=name,
                documentation=documentation,
                labelnames=labelnames,
                registry=self.registry,
                multiprocess_mode='all'
            )
        return self.gauges[name]

    def _get_histogram(self, name, documentation, labelnames, buckets=None):
        if name not in self.histograms:
            kwargs = dict(
                name=name,
                documentation=documentation,
                labelnames=labelnames,
                registry=self.registry,
            )
            if buckets is not None:
                kwargs['buckets'] = buckets
            self.histograms[name] = Histogram(**kwargs)
        return self.histograms[name]

    # =========================================================================
    # Abstract metric methods -- the full union surface.
    # Subclasses implement each with real logic or pass (no-op).
    # =========================================================================

    @abc.abstractmethod
    def collector_name(self) -> str:
        """Return the name of this collector implementation ('legacy', 'canonical')."""
        ...

    @abc.abstractmethod
    def increment_task_poll(self, task_type: str) -> None: ...

    @abc.abstractmethod
    def increment_task_poll_error(self, task_type: str, exception) -> None: ...

    @abc.abstractmethod
    def increment_task_execution_started(self, task_type: str) -> None: ...

    @abc.abstractmethod
    def increment_task_execution_queue_full(self, task_type: str) -> None: ...

    @abc.abstractmethod
    def increment_uncaught_exception(self, exception=None) -> None: ...

    @abc.abstractmethod
    def increment_worker_restart(self, task_type: str) -> None: ...

    @abc.abstractmethod
    def increment_task_paused(self, task_type: str) -> None: ...

    @abc.abstractmethod
    def increment_task_execution_error(self, task_type: str, exception) -> None: ...

    @abc.abstractmethod
    def increment_task_ack_failed(self, task_type: str) -> None: ...

    @abc.abstractmethod
    def increment_task_ack_error(self, task_type: str, exception) -> None: ...

    @abc.abstractmethod
    def increment_task_update_error(self, task_type: str, exception) -> None: ...

    @abc.abstractmethod
    def increment_external_payload_used(self, entity_name: str, operation: str, payload_type: str) -> None: ...

    @abc.abstractmethod
    def increment_workflow_start_error(self, workflow_type: str, exception) -> None: ...

    @abc.abstractmethod
    def record_task_poll_time(self, task_type: str, time_spent: float, status: str = "SUCCESS") -> None: ...

    @abc.abstractmethod
    def record_task_execute_time(self, task_type: str, time_spent: float, status: str = "SUCCESS") -> None: ...

    @abc.abstractmethod
    def record_task_update_time(self, task_type: str, time_spent: float, status: str = "SUCCESS") -> None: ...

    @abc.abstractmethod
    def record_api_request_time(self, method: str, uri: str, status: str, time_spent: float) -> None: ...

    @abc.abstractmethod
    def record_task_result_payload_size(self, task_type: str, payload_size: int) -> None: ...

    @abc.abstractmethod
    def record_workflow_input_payload_size(self, workflow_type: str, version: str, payload_size: int) -> None: ...

    @abc.abstractmethod
    def set_active_workers(self, task_type: str, count: int) -> None: ...

    # =========================================================================
    # Workflow-client hooks.
    # Called by OrkesWorkflowClient on start_workflow paths.  No-ops by
    # default so legacy mode adds zero overhead and emits no new metrics.
    # Canonical overrides these to measure payload size and record errors.
    # =========================================================================

    def measure_workflow_input_payload_size(self, name: str, version, workflow_input) -> None:
        """Measure and record the serialised size of *workflow_input*.  No-op by default."""
        pass

    def measure_workflow_start_error(self, name: str, exception: Exception) -> None:
        """Record a workflow-start error from the client call-site.  No-op by default."""
        pass

    # =========================================================================
    # Concrete event handlers -- delegate to the abstract metric methods.
    # These satisfy the event listener protocols in event/listeners.py.
    # =========================================================================

    def on_poll_started(self, event: PollStarted) -> None:
        self.increment_task_poll(event.task_type)

    def on_poll_completed(self, event: PollCompleted) -> None:
        self.record_task_poll_time(event.task_type, event.duration_ms / 1000, status="SUCCESS")

    def on_poll_failure(self, event: PollFailure) -> None:
        self.increment_task_poll_error(event.task_type, event.cause)
        if hasattr(event, 'duration_ms') and event.duration_ms is not None:
            self.record_task_poll_time(event.task_type, event.duration_ms / 1000, status="FAILURE")

    def on_task_execution_started(self, event: TaskExecutionStarted) -> None:
        self.increment_task_execution_started(event.task_type)
        self._active_worker_counts[event.task_type] += 1
        self.set_active_workers(event.task_type, self._active_worker_counts[event.task_type])

    def on_task_execution_completed(self, event: TaskExecutionCompleted) -> None:
        self.record_task_execute_time(event.task_type, event.duration_ms / 1000, status="SUCCESS")
        if event.output_size_bytes is not None:
            self.record_task_result_payload_size(event.task_type, event.output_size_bytes)
        self._active_worker_counts[event.task_type] = max(0, self._active_worker_counts[event.task_type] - 1)
        self.set_active_workers(event.task_type, self._active_worker_counts[event.task_type])

    def on_task_execution_failure(self, event: TaskExecutionFailure) -> None:
        self.increment_task_execution_error(event.task_type, event.cause)
        if hasattr(event, 'duration_ms') and event.duration_ms is not None:
            self.record_task_execute_time(event.task_type, event.duration_ms / 1000, status="FAILURE")
        self._active_worker_counts[event.task_type] = max(0, self._active_worker_counts[event.task_type] - 1)
        self.set_active_workers(event.task_type, self._active_worker_counts[event.task_type])

    def on_workflow_started(self, event: WorkflowStarted) -> None:
        if not event.success and event.cause is not None:
            self.increment_workflow_start_error(event.name, event.cause)

    def on_workflow_input_payload_size(self, event: WorkflowInputPayloadSize) -> None:
        version_str = str(event.version) if event.version is not None else "1"
        self.record_workflow_input_payload_size(event.name, version_str, event.size_bytes)

    def on_workflow_payload_used(self, event: WorkflowPayloadUsed) -> None:
        self.increment_external_payload_used(event.name, event.operation, event.payload_type)

    def on_task_result_payload_size(self, event: TaskResultPayloadSize) -> None:
        self.record_task_result_payload_size(event.task_type, event.size_bytes)

    def on_task_payload_used(self, event: TaskPayloadUsed) -> None:
        self.increment_external_payload_used(event.task_type, event.operation, event.payload_type)
