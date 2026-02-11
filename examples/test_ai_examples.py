"""
Unit tests for AI workflow examples.

Tests workflow creation, registration, and structure without requiring:
- Running Conductor server
- OpenAI/Anthropic API keys
- PostgreSQL/pgvector database
- MCP weather server
"""

import unittest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conductor.client.configuration.configuration import Configuration
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor


class TestRAGWorkflow(unittest.TestCase):
    """Tests for RAG workflow example."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Configuration(server_api_url="http://localhost:7001/api")
        self.executor = Mock(spec=WorkflowExecutor)
    
    def test_imports(self):
        """Test that all required imports are available."""
        try:
            from conductor.client.workflow.task.llm_tasks import (
                LlmIndexText,
                LlmSearchIndex,
                LlmChatComplete,
                ChatMessage
            )
            from conductor.client.workflow.task.llm_tasks.utils.embedding_model import EmbeddingModel
            from conductor.client.workflow.task.simple_task import SimpleTask
        except ImportError as e:
            self.fail(f"Import failed: {e}")
    
    def test_workflow_creation(self):
        """Test RAG workflow can be created."""
        from conductor.client.workflow.conductor_workflow import ConductorWorkflow
        from conductor.client.workflow.task.llm_tasks import LlmIndexText, LlmSearchIndex, LlmChatComplete
        from conductor.client.workflow.task.llm_tasks.utils.embedding_model import EmbeddingModel
        
        # Create workflow
        wf = ConductorWorkflow(
            executor=self.executor,
            name="test_rag",
            version=1
        )
        
        # Add RAG tasks
        index_task = LlmIndexText(
            task_ref_name="index_doc",
            vector_db="pgvectordb",
            index="test_index",
            embedding_model=EmbeddingModel(provider="openai", model="text-embedding-3-small"),
            text="test text",
            doc_id="test_doc",
            namespace="test_ns"
        )
        
        search_task = LlmSearchIndex(
            task_ref_name="search_kb",
            vector_db="pgvectordb",
            namespace="test_ns",
            index="test_index",
            embedding_model_provider="openai",
            embedding_model="text-embedding-3-small",
            query="test query",
            max_results=5
        )
        
        # Verify tasks created
        self.assertEqual(index_task.task_reference_name, "index_doc")
        self.assertEqual(search_task.task_reference_name, "search_kb")
        
        # Verify input parameters
        self.assertEqual(index_task.input_parameters["vectorDB"], "pgvectordb")
        self.assertEqual(search_task.input_parameters["query"], "test query")


class TestMCPWorkflow(unittest.TestCase):
    """Tests for MCP agent workflow example."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Configuration(server_api_url="http://localhost:7001/api")
        self.executor = Mock(spec=WorkflowExecutor)
    
    def test_imports(self):
        """Test that all required imports are available."""
        try:
            from conductor.client.workflow.task.llm_tasks import (
                ListMcpTools,
                CallMcpTool,
                LlmChatComplete,
                ChatMessage
            )
        except ImportError as e:
            self.fail(f"Import failed: {e}")
    
    def test_workflow_creation(self):
        """Test MCP workflow can be created."""
        from conductor.client.workflow.conductor_workflow import ConductorWorkflow
        from conductor.client.workflow.task.llm_tasks import ListMcpTools, CallMcpTool, LlmChatComplete, ChatMessage
        
        # Create workflow
        wf = ConductorWorkflow(
            executor=self.executor,
            name="test_mcp_agent",
            version=1
        )
        
        mcp_server = "http://localhost:3001/mcp"
        
        # Add MCP tasks
        list_tools = ListMcpTools(
            task_ref_name="discover_tools",
            mcp_server=mcp_server
        )
        
        call_tool = CallMcpTool(
            task_ref_name="execute_tool",
            mcp_server=mcp_server,
            method="test_method"
        )
        
        plan_task = LlmChatComplete(
            task_ref_name="plan_action",
            llm_provider="anthropic",
            model="claude-sonnet-4-20250514",
            messages=[
                ChatMessage(role="system", message="You are an AI agent"),
                ChatMessage(role="user", message="What should I do?")
            ]
        )
        
        # Verify tasks created
        self.assertEqual(list_tools.task_reference_name, "discover_tools")
        self.assertEqual(call_tool.task_reference_name, "execute_tool")
        self.assertEqual(plan_task.task_reference_name, "plan_action")
        
        # Verify input parameters
        self.assertEqual(list_tools.input_parameters["mcpServer"], mcp_server)
        self.assertEqual(call_tool.input_parameters["method"], "test_method")
        self.assertEqual(plan_task.input_parameters["llmProvider"], "anthropic")
    
    def test_mcp_task_serialization(self):
        """Test MCP tasks serialize correctly."""
        from conductor.client.workflow.task.llm_tasks import ListMcpTools, CallMcpTool
        from conductor.client.workflow.task.task_type import TaskType
        
        list_tools = ListMcpTools(
            task_ref_name="list_ref",
            mcp_server="http://test.com/mcp"
        )
        
        # Verify task type (check task_type attribute, not type)
        self.assertEqual(list_tools.task_type, TaskType.LIST_MCP_TOOLS)
        
        # Verify input parameters structure
        self.assertIn("mcpServer", list_tools.input_parameters)
        self.assertEqual(list_tools.input_parameters["mcpServer"], "http://test.com/mcp")
        
        call_tool = CallMcpTool(
            task_ref_name="call_ref",
            mcp_server="http://test.com/mcp",
            method="get_weather",
            arguments={"location": "Tokyo", "units": "celsius"}
        )
        
        # Verify task type
        self.assertEqual(call_tool.task_type, TaskType.CALL_MCP_TOOL)
        
        # Verify all params present
        self.assertIn("mcpServer", call_tool.input_parameters)
        self.assertIn("method", call_tool.input_parameters)
        self.assertIn("arguments", call_tool.input_parameters)
        
        self.assertEqual(call_tool.input_parameters["method"], "get_weather")
        self.assertEqual(call_tool.input_parameters["arguments"]["location"], "Tokyo")
        self.assertEqual(call_tool.input_parameters["arguments"]["units"], "celsius")


class TestChatMessageSerialization(unittest.TestCase):
    """Tests for ChatMessage model."""
    
    def test_chat_message_creation(self):
        """Test ChatMessage can be created and serialized."""
        from conductor.client.workflow.task.llm_tasks import ChatMessage, Role
        
        # Create message
        msg = ChatMessage(
            role="user",
            message="Hello, world!"
        )
        
        # Serialize
        msg_dict = msg.to_dict()
        
        # Verify structure
        self.assertEqual(msg_dict["role"], "user")
        self.assertEqual(msg_dict["message"], "Hello, world!")
        self.assertNotIn("media", msg_dict)  # Should not include empty fields
    
    def test_chat_message_with_media(self):
        """Test ChatMessage with media attachments."""
        from conductor.client.workflow.task.llm_tasks import ChatMessage
        
        msg = ChatMessage(
            role="user",
            message="Describe this image",
            media=["https://example.com/image.jpg"],
            mime_type="image/jpeg"
        )
        
        msg_dict = msg.to_dict()
        
        self.assertEqual(msg_dict["role"], "user")
        self.assertIn("media", msg_dict)
        self.assertEqual(msg_dict["media"], ["https://example.com/image.jpg"])
        self.assertEqual(msg_dict["mimeType"], "image/jpeg")
    
    def test_role_enum(self):
        """Test Role enum values."""
        from conductor.client.workflow.task.llm_tasks import Role
        
        self.assertEqual(Role.USER.value, "user")
        self.assertEqual(Role.ASSISTANT.value, "assistant")
        self.assertEqual(Role.SYSTEM.value, "system")
        self.assertEqual(Role.TOOL_CALL.value, "tool_call")
        self.assertEqual(Role.TOOL.value, "tool")


if __name__ == '__main__':
    unittest.main()
