from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class WorkflowMessage:
    """Represents a message pushed into a running workflow's queue (WMQ).

    Attributes:
        id: UUID assigned by the server on push.
        workflow_id: The workflow instance that owns this message.
        payload: Arbitrary JSON payload supplied by the caller.
        received_at: ISO-8601 UTC timestamp set at ingestion time.
    """

    id: Optional[str] = field(default=None)
    workflow_id: Optional[str] = field(default=None)
    payload: Optional[Dict[str, object]] = field(default=None)
    received_at: Optional[str] = field(default=None)

    swagger_types = {
        'id': 'str',
        'workflow_id': 'str',
        'payload': 'dict(str, object)',
        'received_at': 'str',
    }

    attribute_map = {
        'id': 'id',
        'workflow_id': 'workflowId',
        'payload': 'payload',
        'received_at': 'receivedAt',
    }

    def to_dict(self) -> dict:
        result = {}
        for attr, _ in self.swagger_types.items():
            value = getattr(self, attr)
            if value is not None:
                result[self.attribute_map[attr]] = value
        return result
