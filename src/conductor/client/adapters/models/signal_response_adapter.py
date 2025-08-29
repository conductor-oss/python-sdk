from enum import Enum

from conductor.client.codegen.models.signal_response import SignalResponse


class WorkflowSignalReturnStrategy(Enum):
    """Enum for workflow signal return strategy"""

    TARGET_WORKFLOW = "TARGET_WORKFLOW"
    BLOCKING_WORKFLOW = "BLOCKING_WORKFLOW"
    BLOCKING_TASK = "BLOCKING_TASK"
    BLOCKING_TASK_INPUT = "BLOCKING_TASK_INPUT"


class TaskStatus(Enum):
    """Enum for task status"""

    IN_PROGRESS = "IN_PROGRESS"
    CANCELED = "CANCELED"
    FAILED = "FAILED"
    FAILED_WITH_TERMINAL_ERROR = "FAILED_WITH_TERMINAL_ERROR"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    SCHEDULED = "SCHEDULED"
    TIMED_OUT = "TIMED_OUT"
    READY_FOR_RERUN = "READY_FOR_RERUN"
    SKIPPED = "SKIPPED"


class SignalResponseAdapter(SignalResponse):
    pass
