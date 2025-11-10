from enum import Enum


class MetricName(str, Enum):
    API_REQUEST_TIME = "api_request_time_seconds"
    EXTERNAL_PAYLOAD_USED = "external_payload_used"
    TASK_ACK_ERROR = "task_ack_error"
    TASK_ACK_FAILED = "task_ack_failed"
    TASK_EXECUTE_ERROR = "task_execute_error"
    TASK_EXECUTE_TIME = "task_execute_time"
    TASK_EXECUTE_TIME_HISTOGRAM = "task_execute_time_seconds"
    TASK_EXECUTION_QUEUE_FULL = "task_execution_queue_full"
    TASK_PAUSED = "task_paused"
    TASK_POLL = "task_poll"
    TASK_POLL_TIME = "task_poll_time"
    TASK_POLL_TIME_HISTOGRAM = "task_poll_time_seconds"
    TASK_RESULT_SIZE = "task_result_size"
    TASK_UPDATE_ERROR = "task_update_error"
    TASK_UPDATE_TIME_HISTOGRAM = "task_update_time_seconds"
    THREAD_UNCAUGHT_EXCEPTION = "thread_uncaught_exceptions"
    WORKFLOW_INPUT_SIZE = "workflow_input_size"
    WORKFLOW_START_ERROR = "workflow_start_error"
