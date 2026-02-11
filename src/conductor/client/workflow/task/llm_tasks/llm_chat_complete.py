from __future__ import annotations

from typing import Optional, List, Dict, Any

from typing_extensions import Self

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType

# Re-export ChatMessage for backward compatibility
from conductor.client.workflow.task.llm_tasks.chat_message import ChatMessage, Role  # noqa: F401
from conductor.client.workflow.task.llm_tasks.tool_spec import ToolSpec


class LlmChatComplete(TaskInterface):
    """Executes an LLM chat completion request.

    Sends a conversation (messages) or a prompt template to an LLM provider
    and returns the model's response. Supports tool calling, structured output,
    multi-modal input, and advanced generation parameters.

    Args:
        task_ref_name: Reference name for the task in the workflow.
        llm_provider: AI model integration name (e.g., "openai", "anthropic").
        model: Model identifier (e.g., "gpt-4", "claude-sonnet-4-20250514").
        messages: List of ChatMessage objects for the conversation.
        instructions_template: Prompt template name registered in Conductor.
        template_variables: Variables to substitute in the prompt template.
        prompt_version: Version of the prompt template to use.
        tools: List of ToolSpec objects for function/tool calling.
        user_input: Direct user input text (alternative to messages).
        json_output: If True, request structured JSON output from the model.
        google_search_retrieval: If True, enable Google search grounding (Gemini).
        input_schema: JSON schema for validating input.
        output_schema: JSON schema for structured output.
        output_mime_type: MIME type for the output (e.g., "application/json").
        thinking_token_limit: Max tokens for extended thinking (Anthropic/Gemini).
        reasoning_effort: Reasoning effort level (e.g., "low", "medium", "high").
        output_location: Storage location for output (e.g., S3 path).
        voice: Voice ID for text-to-speech output.
        participants: Map of participant names to their roles.
        stop_words: List of stop sequences for generation.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature (0.0-2.0).
        top_p: Nucleus sampling parameter.
        top_k: Top-k sampling parameter.
        frequency_penalty: Penalize frequent tokens (-2.0 to 2.0).
        presence_penalty: Penalize present tokens (-2.0 to 2.0).
        max_results: Maximum number of results to return.
        task_name: Optional custom task name override.
    """

    def __init__(
        self,
        task_ref_name: str,
        llm_provider: str,
        model: str,
        messages: Optional[List[ChatMessage]] = None,
        instructions_template: Optional[str] = None,
        template_variables: Optional[Dict[str, object]] = None,
        prompt_version: Optional[int] = None,
        tools: Optional[List[ToolSpec]] = None,
        user_input: Optional[str] = None,
        json_output: bool = False,
        google_search_retrieval: bool = False,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        output_mime_type: Optional[str] = None,
        thinking_token_limit: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
        output_location: Optional[str] = None,
        voice: Optional[str] = None,
        participants: Optional[Dict[str, str]] = None,
        stop_words: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        max_results: Optional[int] = None,
        task_name: Optional[str] = None,
    ) -> Self:
        if task_name is None:
            task_name = "llm_chat_complete"

        input_params: Dict[str, Any] = {
            "llmProvider": llm_provider,
            "model": model,
        }

        if template_variables:
            input_params["promptVariables"] = template_variables
        if prompt_version is not None:
            input_params["promptVersion"] = prompt_version

        if messages is not None:
            input_params["messages"] = [
                m.to_dict() if hasattr(m, 'to_dict') else m for m in messages
            ]
        if instructions_template is not None:
            input_params["instructions"] = instructions_template
        if user_input is not None:
            input_params["userInput"] = user_input
        if tools:
            input_params["tools"] = [t.to_dict() if hasattr(t, 'to_dict') else t for t in tools]
        if json_output:
            input_params["jsonOutput"] = json_output
        if google_search_retrieval:
            input_params["googleSearchRetrieval"] = google_search_retrieval
        if input_schema is not None:
            input_params["inputSchema"] = input_schema
        if output_schema is not None:
            input_params["outputSchema"] = output_schema
        if output_mime_type is not None:
            input_params["outputMimeType"] = output_mime_type
        if thinking_token_limit is not None:
            input_params["thinkingTokenLimit"] = thinking_token_limit
        if reasoning_effort is not None:
            input_params["reasoningEffort"] = reasoning_effort
        if output_location is not None:
            input_params["outputLocation"] = output_location
        if voice is not None:
            input_params["voice"] = voice
        if participants:
            input_params["participants"] = participants
        if stop_words:
            input_params["stopWords"] = stop_words
        if max_tokens is not None:
            input_params["maxTokens"] = max_tokens
        if temperature is not None:
            input_params["temperature"] = temperature
        if top_p is not None:
            input_params["topP"] = top_p
        if top_k is not None:
            input_params["topK"] = top_k
        if frequency_penalty is not None:
            input_params["frequencyPenalty"] = frequency_penalty
        if presence_penalty is not None:
            input_params["presencePenalty"] = presence_penalty
        if max_results is not None:
            input_params["maxResults"] = max_results

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_CHAT_COMPLETE,
            input_parameters=input_params,
        )

    def prompt_variables(self, variables: Dict[str, object]) -> Self:
        self.input_parameters.setdefault("promptVariables", {}).update(variables)
        return self

    def prompt_variable(self, variable: str, value: object) -> Self:
        self.input_parameters.setdefault("promptVariables", {})[variable] = value
        return self
