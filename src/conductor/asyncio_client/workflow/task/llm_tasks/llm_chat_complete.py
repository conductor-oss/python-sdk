from __future__ import annotations

from typing import Dict, List, Optional, Union

from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType
from conductor.shared.workflow.models import ChatMessage


class LlmChatComplete(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        llm_provider: str,
        model: str,
        messages: List[Union[ChatMessage, dict]],
        stop_words: Optional[List[str]] = None,
        max_tokens: Optional[int] = 100,
        temperature: int = 0,
        top_p: int = 1,
        instructions_template: Optional[str] = None,
        template_variables: Optional[Dict[str, object]] = None,
    ):
        template_variables = template_variables or {}
        stop_words = stop_words or []

        input_params = {
            "llmProvider": llm_provider,
            "model": model,
            "promptVariables": template_variables,
            "temperature": temperature,
            "topP": top_p,
            "instructions": instructions_template,
            "messages": messages,
        }

        if stop_words:
            input_params["stopWords"] = stop_words
        if max_tokens:
            input_params["maxTokens"] = max_tokens

        super().__init__(
            task_name="llm_chat_complete",
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_CHAT_COMPLETE,
            input_parameters=input_params,
        )

    def prompt_variables(self, variables: Dict[str, object]):
        self.input_parameters["promptVariables"].update(variables)
        return self

    def prompt_variable(self, variable: str, value: object):
        self.input_parameters["promptVariables"][variable] = value
        return self
