from __future__ import annotations

from typing import Optional

from typing_extensions import Self

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class LlmGenerateEmbeddings(TaskInterface):
    """Generates embeddings from text using an LLM provider.

    Converts text into a vector representation using the specified
    embedding model.

    Args:
        task_ref_name: Reference name for the task in the workflow.
        llm_provider: AI model integration name (e.g., "openai").
        model: Embedding model identifier (e.g., "text-embedding-ada-002").
        text: Text to generate embeddings for.
        dimensions: Embedding vector dimensions.
        task_name: Optional custom task name override.
    """

    def __init__(
        self,
        task_ref_name: str,
        llm_provider: str,
        model: str,
        text: str,
        dimensions: Optional[int] = None,
        task_name: Optional[str] = None,
    ) -> Self:
        if task_name is None:
            task_name = "llm_generate_embeddings"

        input_params = {
            "llmProvider": llm_provider,
            "model": model,
            "text": text,
        }

        if dimensions is not None:
            input_params["dimensions"] = dimensions

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_GENERATE_EMBEDDINGS,
            input_parameters=input_params,
        )
