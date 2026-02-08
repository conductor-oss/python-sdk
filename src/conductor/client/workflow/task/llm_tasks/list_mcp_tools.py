from __future__ import annotations

from typing import Optional, Dict

from typing_extensions import Self

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class ListMcpTools(TaskInterface):
    """Lists available tools from an MCP (Model Context Protocol) server.

    Args:
        task_ref_name: Reference name for the task in the workflow.
        mcp_server: MCP server URL (e.g., "http://localhost:3000/sse").
        headers: Optional HTTP headers for the MCP server connection.
        task_name: Optional custom task name.
    """

    def __init__(
        self,
        task_ref_name: str,
        mcp_server: str,
        headers: Optional[Dict[str, str]] = None,
        task_name: Optional[str] = None,
    ) -> Self:
        if task_name is None:
            task_name = "list_mcp_tools"

        input_params = {
            "mcpServer": mcp_server,
        }

        if headers:
            input_params["headers"] = headers

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LIST_MCP_TOOLS,
            input_parameters=input_params,
        )
