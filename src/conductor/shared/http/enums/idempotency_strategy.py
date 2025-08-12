from enum import Enum


class IdempotencyStrategy(str, Enum):
    FAIL = "FAIL",
    RETURN_EXISTING = "RETURN_EXISTING"

    def __str__(self) -> str:
        return self.name.__str__()
