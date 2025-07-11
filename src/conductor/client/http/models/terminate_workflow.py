from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TerminateWorkflow:
    """TerminateWorkflow model for workflow termination operations.

    Attributes:
        workflow_id: The ID of the workflow to terminate
        termination_reason: The reason for terminating the workflow
    """
    workflow_id: Optional[str] = None
    termination_reason: Optional[str] = None

    # Define JSON mapping for serialization
    swagger_types: dict = field(default_factory=lambda: {
        'workflow_id': 'str',
        'termination_reason': 'str'
    })

    attribute_map: dict = field(default_factory=lambda: {
        'workflow_id': 'workflowId',
        'termination_reason': 'terminationReason'
    })

    def to_dict(self):
        """Returns the model properties as a dict"""
        return {
            'workflowId': self.workflow_id,
            'terminationReason': self.termination_reason
        }

    def __repr__(self):
        """Returns string representation of the model"""
        return f"TerminateWorkflow(workflow_id={self.workflow_id!r}, termination_reason={self.termination_reason!r})"