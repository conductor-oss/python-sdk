from enum import Enum

from conductor.client.http.models.start_workflow_request import \
    StartWorkflowRequest


class IdempotencyStrategy(str, Enum):  # shared
    FAIL = ("FAIL",)
    RETURN_EXISTING = "RETURN_EXISTING"

    def __str__(self) -> str:
        return self.name.__str__()


class StartWorkflowRequestAdapter(StartWorkflowRequest):
    pass
