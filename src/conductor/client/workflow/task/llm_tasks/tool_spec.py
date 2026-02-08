from __future__ import annotations

from typing import Optional, Dict, Any


class ToolSpec:
    """Specification for a tool available to an LLM during chat completion.

    Attributes:
        name: Name of the tool.
        type: Type of the tool (e.g., "SIMPLE", "SUB_WORKFLOW").
        description: Human-readable description of the tool.
        config_params: Configuration parameters for the tool.
        integration_names: Map of integration type to integration name.
        input_schema: JSON Schema for the tool's input.
        output_schema: JSON Schema for the tool's output.
    """

    def __init__(
        self,
        name: str,
        type: str = "SIMPLE",
        description: Optional[str] = None,
        config_params: Optional[Dict[str, Any]] = None,
        integration_names: Optional[Dict[str, str]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.type = type
        self.description = description
        self.config_params = config_params or {}
        self.integration_names = integration_names or {}
        self.input_schema = input_schema or {}
        self.output_schema = output_schema or {}

    def to_dict(self) -> dict:
        d: Dict[str, Any] = {"name": self.name, "type": self.type}
        if self.description is not None:
            d["description"] = self.description
        if self.config_params:
            d["configParams"] = self.config_params
        if self.integration_names:
            d["integrationNames"] = self.integration_names
        if self.input_schema:
            d["inputSchema"] = self.input_schema
        if self.output_schema:
            d["outputSchema"] = self.output_schema
        return d
