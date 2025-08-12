from enum import Enum


class AssignmentCompletionStrategy(str, Enum):
    LEAVE_OPEN = ("LEAVE_OPEN",)
    TERMINATE = "TERMINATE"

    def __str__(self) -> str:
        return self.name.__str__()
