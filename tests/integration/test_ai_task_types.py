"""
Integration test: Register workflows with all 13 AI task types against the Conductor server.

This test creates a workflow for each AI/LLM task type, registers it on the server,
then retrieves the workflow definition back to verify correct serialization.
Finally, it cleans up by deleting all test workflows.

Requires a running Conductor server at localhost:7001.
"""

import json
import sys
import unittest

from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor

# Import all AI task types
from conductor.client.workflow.task.llm_tasks import (
    ChatMessage,
    Role,
    ToolSpec,
    ToolCall,
    LlmChatComplete,
    LlmTextComplete,
    LlmGenerateEmbeddings,
    LlmQueryEmbeddings,
    LlmIndexText,
    LlmIndexDocument,
    LlmSearchIndex,
    GenerateImage,
    GenerateAudio,
    LlmStoreEmbeddings,
    LlmSearchEmbeddings,
    ListMcpTools,
    CallMcpTool,
)
from conductor.client.workflow.task.llm_tasks.utils.embedding_model import EmbeddingModel
from conductor.client.workflow.task.task_type import TaskType

# Also verify backward-compatible import path
from conductor.client.workflow.task.llm_tasks.llm_chat_complete import ChatMessage as ChatMessageBC


WORKFLOW_PREFIX = "test_ai_task_type_"


class TestAITaskTypeRegistration(unittest.TestCase):
    """Test that all 13 AI task types can be registered as workflows on the server."""

    @classmethod
    def setUpClass(cls):
        cls.config = Configuration(server_api_url="http://localhost:7001/api")
        cls.clients = OrkesClients(configuration=cls.config)
        cls.executor = WorkflowExecutor(configuration=cls.config)
        cls.metadata_client = cls.clients.get_metadata_client()
        cls.registered_workflows = []

    @classmethod
    def tearDownClass(cls):
        """Clean up all test workflows."""
        for wf_name in cls.registered_workflows:
            try:
                cls.metadata_client.unregister_workflow_def(wf_name, 1)
            except Exception:
                pass

    def _register_and_verify(self, workflow: ConductorWorkflow, expected_task_type: str):
        """Register a workflow and verify it was stored correctly."""
        wf_name = workflow.name
        self.registered_workflows.append(wf_name)

        # Register
        workflow.register(overwrite=True)

        # Retrieve and verify
        wf_def = self.metadata_client.get_workflow_def(wf_name, version=1)
        self.assertIsNotNone(wf_def, f"Workflow {wf_name} not found after registration")

        # Check the task type in the first task
        tasks = wf_def.tasks
        self.assertGreater(len(tasks), 0, f"Workflow {wf_name} has no tasks")
        actual_type = tasks[0].type
        self.assertEqual(
            actual_type,
            expected_task_type,
            f"Task type mismatch for {wf_name}: expected {expected_task_type}, got {actual_type}",
        )
        return wf_def

    # ─── 1. LLM_CHAT_COMPLETE ───────────────────────────────────────────

    def test_01_llm_chat_complete_basic(self):
        """Register a workflow with LlmChatComplete task."""
        wf = ConductorWorkflow(executor=self.executor, name=f"{WORKFLOW_PREFIX}chat_complete_basic", version=1)
        task = LlmChatComplete(
            task_ref_name="chat_ref",
            llm_provider="openai",
            model="gpt-4",
            instructions_template="You are a helpful assistant.",
        )
        wf >> task
        wf_def = self._register_and_verify(wf, "LLM_CHAT_COMPLETE")
        input_params = wf_def.tasks[0].input_parameters
        self.assertEqual(input_params["llmProvider"], "openai")
        self.assertEqual(input_params["model"], "gpt-4")

    def test_02_llm_chat_complete_with_tools(self):
        """Register LlmChatComplete with tools, messages, and new params."""
        tool = ToolSpec(
            name="get_weather",
            type="SIMPLE",
            description="Get weather for a location",
            input_schema={"type": "object", "properties": {"location": {"type": "string"}}},
        )
        msg = ChatMessage(role=Role.USER, message="What's the weather in NYC?")
        wf = ConductorWorkflow(executor=self.executor, name=f"{WORKFLOW_PREFIX}chat_complete_tools", version=1)
        task = LlmChatComplete(
            task_ref_name="chat_tools_ref",
            llm_provider="openai",
            model="gpt-4",
            messages=[msg],
            tools=[tool],
            json_output=True,
            thinking_token_limit=1024,
            reasoning_effort="medium",
            top_k=5,
            frequency_penalty=0.5,
            presence_penalty=0.3,
            max_results=10,
        )
        wf >> task
        wf_def = self._register_and_verify(wf, "LLM_CHAT_COMPLETE")
        input_params = wf_def.tasks[0].input_parameters
        self.assertTrue(input_params.get("jsonOutput"))
        self.assertEqual(input_params.get("thinkingTokenLimit"), 1024)
        self.assertEqual(input_params.get("reasoningEffort"), "medium")
        self.assertIsInstance(input_params.get("tools"), list)
        self.assertEqual(len(input_params["tools"]), 1)

    # ─── 2. LLM_TEXT_COMPLETE ────────────────────────────────────────────

    def test_03_llm_text_complete(self):
        """Register a workflow with LlmTextComplete task."""
        wf = ConductorWorkflow(executor=self.executor, name=f"{WORKFLOW_PREFIX}text_complete", version=1)
        task = LlmTextComplete(
            task_ref_name="text_ref",
            llm_provider="openai",
            model="gpt-3.5-turbo",
            prompt_name="summarize",
            max_tokens=500,
            temperature=0.7,
            top_k=10,
            frequency_penalty=0.2,
            presence_penalty=0.1,
            json_output=True,
        )
        wf >> task
        wf_def = self._register_and_verify(wf, "LLM_TEXT_COMPLETE")
        input_params = wf_def.tasks[0].input_parameters
        self.assertEqual(input_params["promptName"], "summarize")
        self.assertEqual(input_params.get("topK"), 10)
        self.assertTrue(input_params.get("jsonOutput"))

    # ─── 3. LLM_GENERATE_EMBEDDINGS ─────────────────────────────────────

    def test_04_llm_generate_embeddings(self):
        """Register a workflow with LlmGenerateEmbeddings task."""
        wf = ConductorWorkflow(executor=self.executor, name=f"{WORKFLOW_PREFIX}generate_embeddings", version=1)
        task = LlmGenerateEmbeddings(
            task_ref_name="gen_embed_ref",
            llm_provider="openai",
            model="text-embedding-ada-002",
            text="Hello world",
            dimensions=1536,
        )
        wf >> task
        wf_def = self._register_and_verify(wf, "LLM_GENERATE_EMBEDDINGS")
        input_params = wf_def.tasks[0].input_parameters
        self.assertEqual(input_params["dimensions"], 1536)

    # ─── 4. LLM_GET_EMBEDDINGS (LlmQueryEmbeddings) ─────────────────────

    def test_05_llm_query_embeddings(self):
        """Register a workflow with LlmQueryEmbeddings task."""
        wf = ConductorWorkflow(executor=self.executor, name=f"{WORKFLOW_PREFIX}query_embeddings", version=1)
        task = LlmQueryEmbeddings(
            task_ref_name="query_embed_ref",
            vector_db="pineconedb",
            index="my-index",
            embeddings=[0.1, 0.2, 0.3],
            namespace="test-ns",
        )
        wf >> task
        wf_def = self._register_and_verify(wf, "LLM_GET_EMBEDDINGS")
        input_params = wf_def.tasks[0].input_parameters
        self.assertEqual(input_params["vectorDB"], "pineconedb")
        self.assertEqual(input_params["namespace"], "test-ns")

    # ─── 5. LLM_INDEX_TEXT ───────────────────────────────────────────────

    def test_06_llm_index_text(self):
        """Register a workflow with LlmIndexText task."""
        wf = ConductorWorkflow(executor=self.executor, name=f"{WORKFLOW_PREFIX}index_text", version=1)
        task = LlmIndexText(
            task_ref_name="index_text_ref",
            vector_db="pineconedb",
            index="my-index",
            embedding_model=EmbeddingModel(provider="openai", model="text-embedding-ada-002"),
            text="Sample text to index",
            doc_id="doc-001",
            namespace="test-ns",
            chunk_size=1000,
            chunk_overlap=200,
            dimensions=1536,
            url="https://example.com/doc.txt",
        )
        wf >> task
        wf_def = self._register_and_verify(wf, "LLM_INDEX_TEXT")
        input_params = wf_def.tasks[0].input_parameters
        self.assertEqual(input_params["chunkSize"], 1000)
        self.assertEqual(input_params["dimensions"], 1536)
        self.assertEqual(input_params["url"], "https://example.com/doc.txt")

    # ─── 6. LLM_INDEX_DOCUMENT (uses LLM_INDEX_TEXT on server) ──────────

    def test_07_llm_index_document(self):
        """Register a workflow with LlmIndexDocument task (maps to LLM_INDEX_TEXT)."""
        wf = ConductorWorkflow(executor=self.executor, name=f"{WORKFLOW_PREFIX}index_document", version=1)
        task = LlmIndexDocument(
            task_ref_name="index_doc_ref",
            vector_db="pineconedb",
            namespace="test-ns",
            embedding_model=EmbeddingModel(provider="openai", model="text-embedding-ada-002"),
            index="my-index",
            url="https://example.com/doc.pdf",
            media_type="application/pdf",
            dimensions=1536,
        )
        wf >> task
        wf_def = self._register_and_verify(wf, "LLM_INDEX_TEXT")
        input_params = wf_def.tasks[0].input_parameters
        self.assertEqual(input_params["dimensions"], 1536)
        self.assertEqual(input_params["url"], "https://example.com/doc.pdf")
        self.assertEqual(input_params["mediaType"], "application/pdf")

    # ─── 7. LLM_SEARCH_INDEX ────────────────────────────────────────────

    def test_08_llm_search_index(self):
        """Register a workflow with LlmSearchIndex task."""
        wf = ConductorWorkflow(executor=self.executor, name=f"{WORKFLOW_PREFIX}search_index", version=1)
        task = LlmSearchIndex(
            task_ref_name="search_idx_ref",
            vector_db="pineconedb",
            namespace="test-ns",
            index="my-index",
            embedding_model_provider="openai",
            embedding_model="text-embedding-ada-002",
            query="find related documents",
            max_results=5,
            dimensions=1536,
        )
        wf >> task
        wf_def = self._register_and_verify(wf, "LLM_SEARCH_INDEX")
        input_params = wf_def.tasks[0].input_parameters
        self.assertEqual(input_params["dimensions"], 1536)
        self.assertEqual(input_params["maxResults"], 5)

    # ─── 8. GENERATE_IMAGE ──────────────────────────────────────────────

    def test_09_generate_image(self):
        """Register a workflow with GenerateImage task."""
        wf = ConductorWorkflow(executor=self.executor, name=f"{WORKFLOW_PREFIX}generate_image", version=1)
        task = GenerateImage(
            task_ref_name="gen_img_ref",
            llm_provider="openai",
            model="dall-e-3",
            prompt="A sunset over mountains",
            width=1024,
            height=1024,
            style="vivid",
            n=1,
            output_format="png",
        )
        wf >> task
        wf_def = self._register_and_verify(wf, "GENERATE_IMAGE")
        input_params = wf_def.tasks[0].input_parameters
        self.assertEqual(input_params["llmProvider"], "openai")
        self.assertEqual(input_params["prompt"], "A sunset over mountains")
        self.assertEqual(input_params["style"], "vivid")

    # ─── 9. GENERATE_AUDIO ──────────────────────────────────────────────

    def test_10_generate_audio(self):
        """Register a workflow with GenerateAudio task."""
        wf = ConductorWorkflow(executor=self.executor, name=f"{WORKFLOW_PREFIX}generate_audio", version=1)
        task = GenerateAudio(
            task_ref_name="gen_audio_ref",
            llm_provider="openai",
            model="tts-1",
            text="Hello, this is a test.",
            voice="alloy",
            speed=1.0,
            response_format="mp3",
        )
        wf >> task
        wf_def = self._register_and_verify(wf, "GENERATE_AUDIO")
        input_params = wf_def.tasks[0].input_parameters
        self.assertEqual(input_params["text"], "Hello, this is a test.")
        self.assertEqual(input_params["voice"], "alloy")
        self.assertEqual(input_params["responseFormat"], "mp3")

    # ─── 10. LLM_STORE_EMBEDDINGS ────────────────────────────────────────

    def test_11_llm_store_embeddings(self):
        """Register a workflow with LlmStoreEmbeddings task."""
        wf = ConductorWorkflow(executor=self.executor, name=f"{WORKFLOW_PREFIX}store_embeddings", version=1)
        task = LlmStoreEmbeddings(
            task_ref_name="store_embed_ref",
            vector_db="pineconedb",
            index="my-index",
            embeddings=[0.1, 0.2, 0.3, 0.4],
            namespace="test-ns",
            id="doc-123",
            metadata={"source": "test"},
            embedding_model="text-embedding-ada-002",
            embedding_model_provider="openai",
        )
        wf >> task
        wf_def = self._register_and_verify(wf, "LLM_STORE_EMBEDDINGS")
        input_params = wf_def.tasks[0].input_parameters
        self.assertEqual(input_params["vectorDB"], "pineconedb")
        self.assertEqual(input_params["id"], "doc-123")
        self.assertEqual(input_params["embeddingModel"], "text-embedding-ada-002")

    # ─── 11. LLM_SEARCH_EMBEDDINGS ───────────────────────────────────────

    def test_12_llm_search_embeddings(self):
        """Register a workflow with LlmSearchEmbeddings task."""
        wf = ConductorWorkflow(executor=self.executor, name=f"{WORKFLOW_PREFIX}search_embeddings", version=1)
        task = LlmSearchEmbeddings(
            task_ref_name="search_embed_ref",
            vector_db="pineconedb",
            index="my-index",
            embeddings=[0.1, 0.2, 0.3],
            namespace="test-ns",
            max_results=10,
            dimensions=1536,
            embedding_model="text-embedding-ada-002",
            embedding_model_provider="openai",
        )
        wf >> task
        wf_def = self._register_and_verify(wf, "LLM_SEARCH_EMBEDDINGS")
        input_params = wf_def.tasks[0].input_parameters
        self.assertEqual(input_params["maxResults"], 10)
        self.assertEqual(input_params["dimensions"], 1536)

    # ─── 12. LIST_MCP_TOOLS ─────────────────────────────────────────────

    def test_13_list_mcp_tools(self):
        """Register a workflow with ListMcpTools task."""
        wf = ConductorWorkflow(executor=self.executor, name=f"{WORKFLOW_PREFIX}list_mcp_tools", version=1)
        task = ListMcpTools(
            task_ref_name="list_mcp_ref",
            mcp_server="http://localhost:3000/sse",
            headers={"Authorization": "Bearer test-token"},
        )
        wf >> task
        wf_def = self._register_and_verify(wf, "LIST_MCP_TOOLS")
        input_params = wf_def.tasks[0].input_parameters
        self.assertEqual(input_params["mcpServer"], "http://localhost:3000/sse")

    # ─── 13. CALL_MCP_TOOL ──────────────────────────────────────────────

    def test_14_call_mcp_tool(self):
        """Register a workflow with CallMcpTool task."""
        wf = ConductorWorkflow(executor=self.executor, name=f"{WORKFLOW_PREFIX}call_mcp_tool", version=1)
        task = CallMcpTool(
            task_ref_name="call_mcp_ref",
            mcp_server="http://localhost:3000/sse",
            method="get_weather",
            arguments={"location": "New York"},
            headers={"Authorization": "Bearer test-token"},
        )
        wf >> task
        wf_def = self._register_and_verify(wf, "CALL_MCP_TOOL")
        input_params = wf_def.tasks[0].input_parameters
        self.assertEqual(input_params["method"], "get_weather")
        self.assertEqual(input_params["arguments"]["location"], "New York")

    # ─── Backward compatibility ──────────────────────────────────────────

    def test_15_backward_compat_chat_message_import(self):
        """Verify ChatMessage can be imported from the old location."""
        self.assertIs(ChatMessageBC, ChatMessage)

    # ─── Model serialization ────────────────────────────────────────────

    def test_16_chat_message_to_dict(self):
        """Verify ChatMessage serializes correctly."""
        msg = ChatMessage(role=Role.USER, message="Hello")
        d = msg.to_dict()
        self.assertEqual(d["role"], "user")
        self.assertEqual(d["message"], "Hello")

    def test_17_tool_spec_to_dict(self):
        """Verify ToolSpec serializes correctly."""
        spec = ToolSpec(
            name="search",
            type="SIMPLE",
            description="Search the web",
            input_schema={"type": "object"},
        )
        d = spec.to_dict()
        self.assertEqual(d["name"], "search")
        self.assertEqual(d["type"], "SIMPLE")
        self.assertEqual(d["inputSchema"], {"type": "object"})

    def test_18_tool_call_to_dict(self):
        """Verify ToolCall serializes correctly."""
        tc = ToolCall(
            task_reference_name="call_ref",
            name="search",
            type="SIMPLE",
            input_parameters={"query": "test"},
        )
        d = tc.to_dict()
        self.assertEqual(d["taskReferenceName"], "call_ref")
        self.assertEqual(d["name"], "search")
        self.assertEqual(d["inputParameters"], {"query": "test"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
