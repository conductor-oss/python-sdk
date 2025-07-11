from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class UpdateWorkflowVariables:
    """UpdateWorkflowVariables model for updating workflow variables.

    Attributes:
        workflow_id: The ID of the workflow to update
        variables: Map of variable names to their values
        append_array: Whether to append to arrays in existing variables
    """
    workflow_id: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    append_array: Optional[bool] = None

    # Define JSON mapping for serialization
    swagger_types: dict = field(default_factory=lambda: {
        'workflow_id': 'str',
        'variables': 'dict(str, object)',
        'append_array': 'bool'
    })

    attribute_map: dict = field(default_factory=lambda: {
        'workflow_id': 'workflowId',
        'variables': 'variables',
        'append_array': 'appendArray'
    })

    def to_dict(self):
        """Returns the model properties as a dict"""
        return {
            'workflowId': self.workflow_id,
            'variables': self.variables,
            'appendArray': self.append_array
        }

    def __repr__(self):
        """Returns string representation of the model"""
        return f"UpdateWorkflowVariables(workflow_id={self.workflow_id!r}, variables={self.variables!r}, append_array={self.append_array!r})"