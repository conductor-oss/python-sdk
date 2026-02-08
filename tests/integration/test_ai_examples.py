"""
Integration tests: Execute AI example workflows from the Conductor AI README.

These tests create and execute real AI workflows against the Conductor server
using OpenAI and Anthropic providers, plus MCP tool integration.

Requires:
  - Conductor server at localhost:7001 with AI enabled
  - OpenAI and Anthropic API keys configured on the server
  - MCP weather server at localhost:3001
"""

import json
import time
import unittest

from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor

from conductor.client.workflow.task.llm_tasks import (
    ChatMessage,
    Role,
    ToolSpec,
    LlmChatComplete,
    LlmTextComplete,
    LlmGenerateEmbeddings,
    GenerateImage,
    GenerateAudio,
    ListMcpTools,
    CallMcpTool,
)

SERVER_URL = "http://localhost:7001/api"
MCP_SERVER = "http://localhost:3001/mcp"

# Models
OPENAI_CHAT_MODEL = "gpt-4o-mini"
ANTHROPIC_CHAT_MODEL = "claude-sonnet-4-20250514"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_IMAGE_MODEL = "dall-e-3"
OPENAI_TTS_MODEL = "tts-1"

WORKFLOW_PREFIX = "sdk_ai_example_"


class TestAIExamples(unittest.TestCase):
    """Execute all AI example workflows from the Conductor AI README using the Python SDK."""

    @classmethod
    def setUpClass(cls):
        cls.config = Configuration(server_api_url=SERVER_URL)
        cls.clients = OrkesClients(configuration=cls.config)
        cls.executor = WorkflowExecutor(configuration=cls.config)
        cls.metadata_client = cls.clients.get_metadata_client()
        cls.workflow_client = cls.clients.get_workflow_client()
        cls.registered_workflows = []

    @classmethod
    def tearDownClass(cls):
        """Clean up all test workflows."""
        for wf_name in cls.registered_workflows:
            try:
                cls.metadata_client.unregister_workflow_def(wf_name, 1)
            except Exception:
                pass

    def _execute_and_assert(self, workflow: ConductorWorkflow, workflow_input=None,
                            wait_for_seconds=30) -> dict:
        """Execute a workflow synchronously and assert it completed."""
        wf_name = workflow.name
        self.registered_workflows.append(wf_name)

        run = workflow.execute(workflow_input=workflow_input or {},
                               wait_for_seconds=wait_for_seconds)

        status = run.status
        self.assertEqual(
            status, "COMPLETED",
            f"Workflow {wf_name} did not complete. Status: {status}. "
            f"Tasks: {self._task_summary(run)}"
        )
        return run

    def _task_summary(self, run) -> str:
        """Extract task summary for error messages."""
        summaries = []
        for t in (run.tasks or []):
            s = f"{t.reference_task_name}={t.status}"
            if t.reason_for_incompletion:
                s += f" ({t.reason_for_incompletion[:200]})"
            summaries.append(s)
        return "; ".join(summaries)

    def _get_task_output(self, run, task_ref: str) -> dict:
        """Get output data from a specific task in the workflow run."""
        for t in (run.tasks or []):
            if t.reference_task_name == task_ref:
                return t.output_data or {}
        return {}

    # ─── Example 1: Chat Completion ──────────────────────────────────────

    def test_01_chat_completion_openai(self):
        """README Example 1 - Chat completion with OpenAI."""
        wf = ConductorWorkflow(
            executor=self.executor,
            name=f"{WORKFLOW_PREFIX}chat_openai",
            version=1,
        )
        chat = LlmChatComplete(
            task_ref_name="chat",
            llm_provider="openai",
            model=OPENAI_CHAT_MODEL,
            messages=[
                ChatMessage(role=Role.SYSTEM, message="You are a helpful assistant."),
                ChatMessage(role=Role.USER, message="What is the capital of France?"),
            ],
            temperature=0.7,
            max_tokens=500,
        )
        wf >> chat

        run = self._execute_and_assert(wf)
        output = self._get_task_output(run, "chat")

        self.assertIn("result", output)
        result = output["result"].lower()
        self.assertIn("paris", result, f"Expected 'paris' in response, got: {output['result']}")
        print(f"  OpenAI Chat: {output['result'][:100]}")

    def test_02_chat_completion_anthropic(self):
        """README Example 1 variant - Chat completion with Anthropic Claude."""
        wf = ConductorWorkflow(
            executor=self.executor,
            name=f"{WORKFLOW_PREFIX}chat_anthropic",
            version=1,
        )
        chat = LlmChatComplete(
            task_ref_name="chat",
            llm_provider="anthropic",
            model=ANTHROPIC_CHAT_MODEL,
            messages=[
                ChatMessage(role=Role.SYSTEM, message="You are a helpful assistant."),
                ChatMessage(role=Role.USER, message="What is the capital of France?"),
            ],
            temperature=0.7,
            max_tokens=500,
        )
        wf >> chat

        run = self._execute_and_assert(wf)
        output = self._get_task_output(run, "chat")

        self.assertIn("result", output)
        result = output["result"].lower()
        self.assertIn("paris", result, f"Expected 'paris' in response, got: {output['result']}")
        print(f"  Anthropic Chat: {output['result'][:100]}")

    # ─── Example 2: Generate Embeddings ──────────────────────────────────

    def test_03_generate_embeddings(self):
        """README Example 2 - Generate embeddings with OpenAI."""
        wf = ConductorWorkflow(
            executor=self.executor,
            name=f"{WORKFLOW_PREFIX}embeddings",
            version=1,
        )
        embed = LlmGenerateEmbeddings(
            task_ref_name="embeddings",
            llm_provider="openai",
            model=OPENAI_EMBEDDING_MODEL,
            text="Conductor is an orchestration platform",
        )
        wf >> embed

        run = self._execute_and_assert(wf)
        output = self._get_task_output(run, "embeddings")

        self.assertIn("result", output)
        embeddings = output["result"]
        self.assertIsInstance(embeddings, list, "Embeddings should be a list")
        self.assertGreater(len(embeddings), 100, f"Expected high-dimensional vector, got {len(embeddings)} dims")
        self.assertIsInstance(embeddings[0], float, "Each element should be a float")
        print(f"  Embeddings: {len(embeddings)} dimensions, first 3: {embeddings[:3]}")

    # ─── Example 3: Image Generation ─────────────────────────────────────

    def test_04_image_generation(self):
        """README Example 3 - Generate image with OpenAI DALL-E."""
        wf = ConductorWorkflow(
            executor=self.executor,
            name=f"{WORKFLOW_PREFIX}image_gen",
            version=1,
        )
        img = GenerateImage(
            task_ref_name="image",
            llm_provider="openai",
            model=OPENAI_IMAGE_MODEL,
            prompt="A futuristic cityscape at sunset",
            width=1024,
            height=1024,
            n=1,
            style="vivid",
        )
        wf >> img

        run = self._execute_and_assert(wf)
        output = self._get_task_output(run, "image")

        # DALL-E returns url, b64_json, media array, or result
        has_result = (output.get("url") or output.get("b64_json")
                      or output.get("result") or output.get("media"))
        self.assertTrue(has_result, f"Expected image output, got: {list(output.keys())}")
        print(f"  Image output keys: {list(output.keys())}")
        if output.get("url"):
            print(f"  Image URL: {output['url'][:100]}...")
        if output.get("media"):
            print(f"  Image media: {str(output['media'])[:200]}")

    # ─── Example 4: Audio Generation (TTS) ───────────────────────────────

    def test_05_audio_generation(self):
        """README Example 4 - Text-to-speech with OpenAI."""
        wf = ConductorWorkflow(
            executor=self.executor,
            name=f"{WORKFLOW_PREFIX}tts",
            version=1,
        )
        audio = GenerateAudio(
            task_ref_name="audio",
            llm_provider="openai",
            model=OPENAI_TTS_MODEL,
            text="Hello, this is a test of text to speech.",
            voice="alloy",
            speed=1.0,
            response_format="mp3",
        )
        wf >> audio

        run = self._execute_and_assert(wf)
        output = self._get_task_output(run, "audio")

        # TTS returns a URL, audio data, media, or result
        has_result = (output.get("url") or output.get("result")
                      or output.get("format") or output.get("media"))
        self.assertTrue(has_result, f"Expected audio output, got: {list(output.keys())}")
        print(f"  Audio output keys: {list(output.keys())}")

    # ─── Example 7a: MCP - List Tools ────────────────────────────────────

    def test_06_mcp_list_tools(self):
        """README Example 7 - List tools from MCP server."""
        wf = ConductorWorkflow(
            executor=self.executor,
            name=f"{WORKFLOW_PREFIX}mcp_list",
            version=1,
        )
        list_tools = ListMcpTools(
            task_ref_name="list_tools",
            mcp_server=MCP_SERVER,
        )
        wf >> list_tools

        run = self._execute_and_assert(wf)
        output = self._get_task_output(run, "list_tools")

        self.assertIn("tools", output, f"Expected 'tools' in output, got: {list(output.keys())}")
        tools = output["tools"]
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0, "Expected at least one tool")

        tool_names = [t["name"] for t in tools]
        self.assertIn("get_current_weather", tool_names)
        print(f"  MCP Tools found: {tool_names}")

    # ─── Example 7b: MCP - Call Tool ─────────────────────────────────────

    def test_07_mcp_call_tool(self):
        """README Example 7 - Call MCP weather tool directly."""
        wf = ConductorWorkflow(
            executor=self.executor,
            name=f"{WORKFLOW_PREFIX}mcp_call",
            version=1,
        )
        call = CallMcpTool(
            task_ref_name="weather",
            mcp_server=MCP_SERVER,
            method="get_current_weather",
            arguments={"city": "New York"},
        )
        wf >> call

        run = self._execute_and_assert(wf)
        output = self._get_task_output(run, "weather")

        # MCP returns content array
        self.assertIn("content", output, f"Expected 'content' in output, got: {list(output.keys())}")
        content = output["content"]
        self.assertIsInstance(content, list)
        self.assertGreater(len(content), 0)

        # Check for weather data in the text response
        text = content[0].get("text", "")
        self.assertTrue(len(text) > 0, "Expected non-empty weather response")
        print(f"  MCP Weather: {text[:200]}")

    # ─── Example 8: MCP + AI Agent Workflow ──────────────────────────────

    def test_08_mcp_ai_agent(self):
        """README Example 8 - MCP + AI Agent: discover tools, plan, execute, summarize."""
        wf = ConductorWorkflow(
            executor=self.executor,
            name=f"{WORKFLOW_PREFIX}mcp_agent",
            version=1,
        )

        # Step 1: Discover available tools from MCP server
        discover = ListMcpTools(
            task_ref_name="discover_tools",
            mcp_server=MCP_SERVER,
        )

        # Step 2: LLM decides which tool to use (using Anthropic)
        plan = LlmChatComplete(
            task_ref_name="plan",
            llm_provider="anthropic",
            model=ANTHROPIC_CHAT_MODEL,
            messages=[
                ChatMessage(
                    role=Role.SYSTEM,
                    message="You are an AI agent. Available tools: ${discover_tools.output.tools}. "
                            "The user wants to: ${workflow.input.task}. "
                            "Respond with ONLY a JSON object (no markdown, no explanation): "
                            "{\"method\": \"<tool_name>\", \"arguments\": {<args>}}"
                ),
                ChatMessage(
                    role=Role.USER,
                    message="Which tool should I use and what parameters?"
                ),
            ],
            temperature=0.1,
            max_tokens=500,
        )

        # Step 3: Execute the chosen tool
        execute = CallMcpTool(
            task_ref_name="execute",
            mcp_server=MCP_SERVER,
            method="get_current_weather",
            arguments={"city": "${workflow.input.city}"},
        )

        # Step 4: Summarize the result
        summarize = LlmChatComplete(
            task_ref_name="summarize",
            llm_provider="openai",
            model=OPENAI_CHAT_MODEL,
            messages=[
                ChatMessage(
                    role=Role.USER,
                    message="Summarize this weather result for the user in one sentence: "
                            "${execute.output.content}"
                ),
            ],
            max_tokens=200,
        )

        wf >> discover >> plan >> execute >> summarize

        run = self._execute_and_assert(
            wf,
            workflow_input={"task": "Get the current weather in San Francisco", "city": "San Francisco"},
        )

        # Verify each step completed
        discover_out = self._get_task_output(run, "discover_tools")
        self.assertIn("tools", discover_out)
        print(f"  Step 1 - Discovered {len(discover_out['tools'])} tools")

        plan_out = self._get_task_output(run, "plan")
        self.assertIn("result", plan_out)
        print(f"  Step 2 - Plan: {str(plan_out['result'])[:150]}")

        execute_out = self._get_task_output(run, "execute")
        self.assertIn("content", execute_out)
        print(f"  Step 3 - Weather: {execute_out['content'][0].get('text', '')[:150]}")

        summarize_out = self._get_task_output(run, "summarize")
        self.assertIn("result", summarize_out)
        print(f"  Step 4 - Summary: {summarize_out['result'][:150]}")

    # ─── Example: LLM with tool calling ──────────────────────────────────

    def test_09_chat_with_tool_definitions(self):
        """README Example - LLM Chat Complete with tool definitions (function calling)."""
        wf = ConductorWorkflow(
            executor=self.executor,
            name=f"{WORKFLOW_PREFIX}chat_tools",
            version=1,
        )

        weather_tool = ToolSpec(
            name="get_current_weather",
            type="MCP_TOOL",
            description="Get current weather for a city",
            config_params={"mcpServer": MCP_SERVER},
            input_schema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name in English",
                    }
                },
                "required": ["city"],
            },
        )

        chat = LlmChatComplete(
            task_ref_name="chat",
            llm_provider="openai",
            model=OPENAI_CHAT_MODEL,
            messages=[
                ChatMessage(
                    role=Role.SYSTEM,
                    message="You are a helpful assistant with access to weather tools.",
                ),
                ChatMessage(
                    role=Role.USER,
                    message="What is the weather like in Tokyo right now?",
                ),
            ],
            tools=[weather_tool],
            temperature=0.1,
            max_tokens=500,
        )
        wf >> chat

        run = self._execute_and_assert(wf)
        output = self._get_task_output(run, "chat")

        # The LLM may either call the tool (TOOL_CALLS) or respond directly
        finish_reason = output.get("finishReason", "")
        result = output.get("result", "")
        tool_calls = output.get("toolCalls", [])

        print(f"  Finish reason: {finish_reason}")
        if tool_calls:
            print(f"  Tool calls: {json.dumps(tool_calls, indent=2)[:300]}")
        if result:
            print(f"  Result: {str(result)[:200]}")

        # Either the LLM called the tool or gave a direct response - both are valid
        self.assertTrue(
            finish_reason in ("STOP", "TOOL_CALLS", "stop", "tool_calls", "end_turn") or result,
            f"Expected valid finish reason or result, got finishReason={finish_reason}, result={result}"
        )

    # ─── Multi-provider comparison ───────────────────────────────────────

    def test_10_multi_provider_comparison(self):
        """Bonus: Same question to both OpenAI and Anthropic, compare responses."""
        wf = ConductorWorkflow(
            executor=self.executor,
            name=f"{WORKFLOW_PREFIX}multi_provider",
            version=1,
        )

        openai_chat = LlmChatComplete(
            task_ref_name="openai_answer",
            llm_provider="openai",
            model=OPENAI_CHAT_MODEL,
            messages=[
                ChatMessage(role=Role.USER, message="In one sentence, what is workflow orchestration?"),
            ],
            max_tokens=100,
        )

        anthropic_chat = LlmChatComplete(
            task_ref_name="anthropic_answer",
            llm_provider="anthropic",
            model=ANTHROPIC_CHAT_MODEL,
            messages=[
                ChatMessage(role=Role.USER, message="In one sentence, what is workflow orchestration?"),
            ],
            max_tokens=100,
        )

        wf >> openai_chat >> anthropic_chat

        run = self._execute_and_assert(wf)

        openai_out = self._get_task_output(run, "openai_answer")
        anthropic_out = self._get_task_output(run, "anthropic_answer")

        self.assertIn("result", openai_out)
        self.assertIn("result", anthropic_out)

        print(f"  OpenAI:    {openai_out['result'][:150]}")
        print(f"  Anthropic: {anthropic_out['result'][:150]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
