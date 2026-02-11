from __future__ import annotations

from typing import Optional, Dict, Any

from typing_extensions import Self

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class GenerateImage(TaskInterface):
    """Generates images using an LLM provider.

    Args:
        task_ref_name: Reference name for the task in the workflow.
        llm_provider: AI provider integration name (e.g., "openai").
        model: Model name (e.g., "dall-e-3").
        prompt: Image generation prompt.
        width: Image width in pixels (default: 1024).
        height: Image height in pixels (default: 1024).
        size: Size specification (alternative to width/height, e.g., "1024x1024").
        style: Image style (e.g., "natural", "vivid").
        n: Number of images to generate (default: 1).
        weight: Image weight parameter.
        output_format: Output format - "jpg", "png", or "webp" (default: "png").
        prompt_variables: Variables for prompt template substitution.
        task_name: Optional custom task name.
    """

    def __init__(
        self,
        task_ref_name: str,
        llm_provider: str,
        model: str,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        size: Optional[str] = None,
        style: Optional[str] = None,
        n: int = 1,
        weight: Optional[float] = None,
        output_format: str = "png",
        prompt_variables: Optional[Dict[str, Any]] = None,
        task_name: Optional[str] = None,
    ) -> Self:
        if task_name is None:
            task_name = "generate_image"

        input_params: Dict[str, Any] = {
            "llmProvider": llm_provider,
            "model": model,
            "prompt": prompt,
            "width": width,
            "height": height,
            "n": n,
            "outputFormat": output_format,
        }

        if size is not None:
            input_params["size"] = size
        if style is not None:
            input_params["style"] = style
        if weight is not None:
            input_params["weight"] = weight
        if prompt_variables:
            input_params["promptVariables"] = prompt_variables

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.GENERATE_IMAGE,
            input_parameters=input_params,
        )
