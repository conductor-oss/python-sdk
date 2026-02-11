from __future__ import annotations

from typing import Optional, Dict, Any

from typing_extensions import Self

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class CallMcpTool(TaskInterface):
    """Calls a specific tool on an MCP (Model Context Protocol) server.

    Args:
        task_ref_name: Reference name for the task in the workflow.
        mcp_server: MCP server URL.
        method: Name of the tool to call.
        arguments: Arguments to pass to the tool.
        headers: Optional HTTP headers for the MCP server connection.
        task_name: Optional custom task name.
    """

    def __init__(
        self,
        task_ref_name: str,
        mcp_server: str,
        method: str,
        arguments: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        task_name: Optional[str] = None,
    ) -> Self:
        if task_name is None:
            task_name = "call_mcp_tool"

        input_params: Dict[str, Any] = {
            "mcpServer": mcp_server,
            "method": method,
            "arguments": arguments or {},
        }

        if headers:
            input_params["headers"] = headers

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.CALL_MCP_TOOL,
            input_parameters=input_params,
        )
