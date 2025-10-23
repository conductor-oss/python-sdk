from __future__ import annotations

from typing import Dict, List, Optional, Any

from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType


class LlmTextComplete(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        llm_provider: str,
        model: str,
        prompt_name: str,
        stop_words: Optional[List[str]] = None,
        max_tokens: Optional[int] = 100,
        temperature: int = 0,
        top_p: int = 1,
        task_name: Optional[str] = None,
    ):
        stop_words = stop_words or []
        optional_input_params: Dict[str, Any] = {}

        if stop_words:
            optional_input_params.update({"stopWords": stop_words})

        if max_tokens:
            optional_input_params.update({"maxTokens": max_tokens})

        if not task_name:
            task_name = "llm_text_complete"

        input_params: Dict[str, Any] = {
            "llmProvider": llm_provider,
            "model": model,
            "promptName": prompt_name,
            "promptVariables": {},
            "temperature": temperature,
            "topP": top_p,
        }

        input_params.update(optional_input_params)

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_TEXT_COMPLETE,
            input_parameters=input_params,
        )
        self.input_parameters["promptVariables"] = {}

    def prompt_variables(self, variables: Dict[str, object]):
        self.input_parameters["promptVariables"].update(variables)
        return self

    def prompt_variable(self, variable: str, value: object):
        self.input_parameters["promptVariables"][variable] = value
        return self
