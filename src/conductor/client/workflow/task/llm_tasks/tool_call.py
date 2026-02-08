from __future__ import annotations

from typing import Optional, Dict, Any


class ToolCall:
    """Represents a tool call made by an LLM during chat completion.

    Attributes:
        task_reference_name: Reference name for the task in a workflow.
        name: Name of the tool being called.
        integration_names: Map of integration type to integration name.
        type: Task type for execution (default: "SIMPLE").
        input_parameters: Input parameters for the tool call.
        output: Output from the tool execution.
    """

    def __init__(
        self,
        name: str,
        task_reference_name: Optional[str] = None,
        integration_names: Optional[Dict[str, str]] = None,
        type: str = "SIMPLE",
        input_parameters: Optional[Dict[str, Any]] = None,
        output: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.task_reference_name = task_reference_name
        self.name = name
        self.integration_names = integration_names or {}
        self.type = type
        self.input_parameters = input_parameters or {}
        self.output = output or {}

    def to_dict(self) -> dict:
        d: Dict[str, Any] = {"name": self.name, "type": self.type}
        if self.task_reference_name is not None:
            d["taskReferenceName"] = self.task_reference_name
        if self.integration_names:
            d["integrationNames"] = self.integration_names
        if self.input_parameters:
            d["inputParameters"] = self.input_parameters
        if self.output:
            d["output"] = self.output
        return d
