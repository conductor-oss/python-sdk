from enum import Enum


class TriggerType(str, Enum):
    ASSIGNED = ("ASSIGNED",)
    PENDING = ("PENDING",)
    IN_PROGRESS = ("IN_PROGRESS",)
    COMPLETED = ("COMPLETED",)
    TIMED_OUT = ("TIMED_OUT",)
    ASSIGNEE_CHANGED = ("ASSIGNEE_CHANGED",)

    def __str__(self) -> str:
        return self.name.__str__()
