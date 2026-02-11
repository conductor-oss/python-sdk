from __future__ import annotations

from typing import Optional, List, Dict, Any

from typing_extensions import Self

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class LlmTextComplete(TaskInterface):
    """Executes an LLM text completion request using a prompt template.

    Sends a prompt template with variables to an LLM provider and returns
    the model's text completion response.

    Args:
        task_ref_name: Reference name for the task in the workflow.
        llm_provider: AI model integration name (e.g., "openai", "anthropic").
        model: Model identifier (e.g., "gpt-4", "claude-sonnet-4-20250514").
        prompt_name: Name of the prompt template registered in Conductor.
        prompt_version: Version of the prompt template to use.
        stop_words: List of stop sequences for generation.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature (0.0-2.0).
        top_p: Nucleus sampling parameter.
        top_k: Top-k sampling parameter.
        frequency_penalty: Penalize frequent tokens (-2.0 to 2.0).
        presence_penalty: Penalize present tokens (-2.0 to 2.0).
        max_results: Maximum number of results to return.
        json_output: If True, request structured JSON output from the model.
        task_name: Optional custom task name override.
    """

    def __init__(
        self,
        task_ref_name: str,
        llm_provider: str,
        model: str,
        prompt_name: str,
        prompt_version: Optional[int] = None,
        stop_words: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        max_results: Optional[int] = None,
        json_output: bool = False,
        task_name: Optional[str] = None,
    ) -> Self:
        if not task_name:
            task_name = "llm_text_complete"

        input_params: Dict[str, Any] = {
            "llmProvider": llm_provider,
            "model": model,
            "promptName": prompt_name,
        }

        if prompt_version is not None:
            input_params["promptVersion"] = prompt_version
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
        if json_output:
            input_params["jsonOutput"] = json_output

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_TEXT_COMPLETE,
            input_parameters=input_params,
        )

    def prompt_variables(self, variables: Dict[str, object]) -> Self:
        self.input_parameters.setdefault("promptVariables", {}).update(variables)
        return self

    def prompt_variable(self, variable: str, value: object) -> Self:
        self.input_parameters.setdefault("promptVariables", {})[variable] = value
        return self
