from enum import Enum


class WorkflowStatus(str, Enum):
    COMPLETED = ("COMPLETED",)
    FAILED = ("FAILED",)
    PAUSED = ("PAUSED",)
    RUNNING = ("RUNNING",)
    TERMINATED = ("TERMINATED",)
    TIMEOUT_OUT = ("TIMED_OUT",)
