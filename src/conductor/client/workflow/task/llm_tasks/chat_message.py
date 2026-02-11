from __future__ import annotations

from enum import Enum
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from conductor.client.workflow.task.llm_tasks.tool_call import ToolCall


class Role(str, Enum):
    """Roles for participants in a chat conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL_CALL = "tool_call"
    TOOL = "tool"


class ChatMessage:
    """Represents a message in a chat conversation.

    Attributes:
        role: The role of the message sender (user, assistant, system, tool_call, tool).
        message: The text content of the message.
        media: List of media URLs attached to the message.
        mime_type: MIME type of the media content.
        tool_calls: List of tool calls associated with the message.
    """

    def __init__(
        self,
        role: str,
        message: str,
        media: Optional[List[str]] = None,
        mime_type: Optional[str] = None,
        tool_calls: Optional[List[ToolCall]] = None,
    ) -> None:
        self.role = role
        self.message = message
        self.media = media or []
        self.mime_type = mime_type
        self.tool_calls = tool_calls

    def to_dict(self) -> dict:
        d = {"role": self.role, "message": self.message}
        if self.media:
            d["media"] = self.media
        if self.mime_type is not None:
            d["mimeType"] = self.mime_type
        if self.tool_calls:
            d["toolCalls"] = [tc.to_dict() for tc in self.tool_calls]
        return d
