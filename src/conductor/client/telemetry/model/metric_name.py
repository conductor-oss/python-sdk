from enum import Enum


class MetricName(str, Enum):
    # Canonical HTTP client request timing (real Histogram: _bucket/_count/_sum).
    # Renamed from the legacy "http_api_client_request" Gauge-with-quantile shape.
    # See sdk-metrics-harmonization.md for details.
    API_REQUEST_TIME = "http_api_client_request_seconds"
    EXTERNAL_PAYLOAD_USED = "external_payload_used"
    TASK_ACK_ERROR = "task_ack_error"
    TASK_ACK_FAILED = "task_ack_failed"
    TASK_EXECUTE_ERROR = "task_execute_error"
    TASK_EXECUTE_TIME = "task_execute_time"
    TASK_EXECUTE_TIME_HISTOGRAM = "task_execute_time_seconds"
    TASK_EXECUTION_QUEUE_FULL = "task_execution_queue_full"
    TASK_EXECUTION_STARTED = "task_execution_started"
    TASK_PAUSED = "task_paused"
    TASK_POLL = "task_poll"
    TASK_POLL_ERROR = "task_poll_error"
    TASK_POLL_TIME = "task_poll_time"
    TASK_POLL_TIME_HISTOGRAM = "task_poll_time_seconds"
    TASK_RESULT_SIZE = "task_result_size"
    TASK_RESULT_SIZE_BYTES = "task_result_size_bytes"
    TASK_UPDATE_ERROR = "task_update_error"
    TASK_UPDATE_TIME_HISTOGRAM = "task_update_time_seconds"
    THREAD_UNCAUGHT_EXCEPTION = "thread_uncaught_exceptions"
    WORKER_RESTART = "worker_restart"
    WORKFLOW_INPUT_SIZE = "workflow_input_size"
    WORKFLOW_INPUT_SIZE_BYTES = "workflow_input_size_bytes"
    WORKFLOW_START_ERROR = "workflow_start_error"
