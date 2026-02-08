from __future__ import annotations

from typing import Optional, Dict, Any

from typing_extensions import Self

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class GenerateAudio(TaskInterface):
    """Generates audio (text-to-speech) using an LLM provider.

    Args:
        task_ref_name: Reference name for the task in the workflow.
        llm_provider: AI provider integration name.
        model: Model name (e.g., "tts-1").
        text: Text content to convert to speech.
        voice: Voice identifier.
        speed: Speech speed multiplier.
        response_format: Audio format (e.g., "mp3", "wav").
        n: Number of audio outputs to generate (default: 1).
        prompt: Alternative prompt text.
        prompt_variables: Variables for prompt template substitution.
        task_name: Optional custom task name.
    """

    def __init__(
        self,
        task_ref_name: str,
        llm_provider: str,
        model: str,
        text: Optional[str] = None,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        response_format: Optional[str] = None,
        n: int = 1,
        prompt: Optional[str] = None,
        prompt_variables: Optional[Dict[str, Any]] = None,
        task_name: Optional[str] = None,
    ) -> Self:
        if task_name is None:
            task_name = "generate_audio"

        input_params: Dict[str, Any] = {
            "llmProvider": llm_provider,
            "model": model,
            "n": n,
        }

        if text is not None:
            input_params["text"] = text
        if voice is not None:
            input_params["voice"] = voice
        if speed is not None:
            input_params["speed"] = speed
        if response_format is not None:
            input_params["responseFormat"] = response_format
        if prompt is not None:
            input_params["prompt"] = prompt
        if prompt_variables:
            input_params["promptVariables"] = prompt_variables

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.GENERATE_AUDIO,
            input_parameters=input_params,
        )
